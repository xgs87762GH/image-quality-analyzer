"""
分析 WebSocket 服务（高内聚：WebSocket 分析逻辑集中）

批次化分析：同一 client_id 下仅有一个进行中的批次；新请求追加到该批次。
"""
import threading
import time
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import request
from flask_socketio import emit, join_room

from utils.logger import get_logger
from database.connection import get_db
from services.image_service import ImageService
from repositories.image_repository import ImageRepository
from backend.websocket.analysis_cache import analysis_cache
from backend.websocket.message_format import (
    create_analysis_progress_message,
    create_analysis_complete_message,
    create_analysis_error_message,
    create_analysis_started_message,
    create_analysis_appended_message
)
from backend.websocket.message_codes import MessageCode
from backend.websocket.unified_message import create_unified_message


def start_analysis_batch(
    socketio,
    client_id: str,
    image_ids: list[int],
    settings: Dict[str, Any],
) -> str:
    """
    Start an analysis batch for a client.

    This function is intentionally reusable by both:
    - WebSocket: `start_analysis` event handler
    - REST API: `POST /api/images/analyze`
    """
    logger = get_logger()
    analysis_room = f"analysis_{client_id}"

    task_id = analysis_cache.create_task(client_id, image_ids, settings)

    # Legacy + v2 started notifications (double channel, compatibility)
    try:
        section = analysis_cache.get_section(task_id)
        started_message = create_analysis_started_message(len(image_ids), task_id, section=section)
        socketio.emit("analysis_started", started_message, room=analysis_room)
    except Exception:
        pass

    socketio.emit(
        "batch_update",
        create_unified_message(
            type="image_analysis",
            code=MessageCode.ANALYSIS_STARTED,
            message="Batch analysis started",
            data={
                "batch_id": task_id,
                "total": len(image_ids),
                "status": "running",
                "batch_status": {
                    "pending_count": len(image_ids),
                    "running_count": 0,
                    "completed_count": 0,
                    "failed_count": 0,
                    "total": len(image_ids),
                },
            },
        ),
        room=analysis_room,
    )

    # Start background worker thread.
    # We keep the logic simple and rely on analysis_cache for truth.
    def _worker() -> None:
        import queue as queue_module

        try:
            task = analysis_cache.get_task(task_id)
            if not task:
                logger.error(f"[WebSocket] Task not found: task_id={task_id}")
                return

            task_settings = task.settings
            evaluation_questions = list(task_settings.get("evaluation_questions") or [])
            aesthetic_mode = task_settings.get("aesthetic_mode", "none")
            if aesthetic_mode == "clip":
                evaluation_questions = []
                logger.debug("[WebSocket] aesthetic_mode=clip, evaluation_questions ignored")

            concurrent_count = max(1, min(10, int(task_settings.get("concurrentCount", 1))))
            write_xmp = task_settings.get("write_xmp", True)

            ai_analyzer = None
            if aesthetic_mode == "ai" or evaluation_questions:
                from services.service_factory import ServiceFactory

                ai_analyzer = ServiceFactory.create_ai_analyzer(
                    model=task_settings.get("ai_model", "ollama"),
                    api_key=task_settings.get("ai_api_key"),
                    ollama_base_url=task_settings.get("ollama_base_url", "http://localhost:11434"),
                    ollama_model=task_settings.get("ollama_model", "llama3.2-vision"),
                )

            def analyze_one(image_id: int) -> Dict[str, Any]:
                thread_db = get_db()
                repo = ImageRepository(thread_db)
                svc = ImageService(aesthetic_mode=aesthetic_mode, ai_analyzer=ai_analyzer)

                analysis_cache.add_to_section(task_id, image_id)
                analysis_cache.update_image_status(task_id, image_id, "analyzing", success=False)

                task_now = analysis_cache.get_task(task_id)
                if task_now:
                    processed = task_now.success_count + task_now.fail_count
                    _emit_progress(
                        socketio,
                        analysis_room,
                        image_id,
                        processed,
                        task_now.total,
                        task_now.success_count,
                        task_now.fail_count,
                        "analyzing",
                        task_id=task_id,
                    )

                image = repo.find_by_id(image_id)
                if not image:
                    analysis_cache.remove_from_section(task_id, image_id)
                    analysis_cache.update_image_status(task_id, image_id, "error", success=False, error="Image not found")
                    return {"image_id": image_id, "success": False, "error": "Image not found"}

                # 处理图像（基础分析）
                process_result = svc.process_image(image.file_path, write_xmp=write_xmp) or {}
                if not process_result.get("success"):
                    error_msg = process_result.get("error", "图像处理失败")
                    analysis_cache.remove_from_section(task_id, image_id)
                    analysis_cache.update_image_status(task_id, image_id, "error", success=False, error=error_msg)
                    return {"image_id": image_id, "success": False, "error": error_msg}
                
                # 获取完整的质量分析结果（从数据库）
                quality = svc.quality_repo.find_by_image_id(image.id)
                quality_dict = quality.to_dict() if quality else {}
                
                # 构建符合 REFACTOR_PLAN.md 规范的 result 结构
                base_result = {
                    "quality": quality_dict,  # 完整的质量分析结果
                    "aesthetic_score": quality_dict.get("aesthetic_score") if quality_dict else None,
                }
                
                # Optional AI deep analysis
                if ai_analyzer and (aesthetic_mode == "ai" or evaluation_questions):
                    try:
                        ai_result = ai_analyzer.analyze_image(image.file_path, evaluation_questions=evaluation_questions)
                        if ai_result.get("success"):
                            ai_analysis_text = ai_result.get("analysis")
                            evaluations_data = ai_result.get("evaluations")
                            
                            # Convert ai_analysis to string if it's a dict
                            if isinstance(ai_analysis_text, dict):
                                import json
                                ai_analysis_text = json.dumps(ai_analysis_text, ensure_ascii=False)
                            
                            # Convert evaluations to JSON string if it's a list
                            evaluations_json = None
                            if evaluations_data:
                                import json
                                evaluations_json = json.dumps(evaluations_data, ensure_ascii=False)
                            
                            base_result["ai_analysis"] = ai_analysis_text
                            base_result["evaluations"] = evaluations_data  # Keep as list for WebSocket response
                            
                            # Save AI analysis results to database
                            metadata_repo = svc.metadata_repo
                            existing_metadata = metadata_repo.find_by_image_id(image.id)
                            
                            if existing_metadata:
                                # Update existing metadata
                                existing_metadata.ai_analysis = ai_analysis_text
                                existing_metadata.evaluations = evaluations_json
                                metadata_repo.update(existing_metadata)
                                logger.info(
                                    f"[WebSocket] AI analysis results saved to database | "
                                    f"image_id={image_id} | "
                                    f"has_ai_analysis={bool(ai_analysis_text)} | "
                                    f"has_evaluations={bool(evaluations_json)}"
                                )
                            else:
                                # Create new metadata with AI analysis
                                xmp_data = {
                                    'ai_analysis': ai_analysis_text,
                                    'evaluations': evaluations_json
                                }
                                metadata_repo.create_or_update(image.id, xmp_data)
                                logger.info(
                                    f"[WebSocket] New metadata created with AI analysis | "
                                    f"image_id={image_id}"
                                )
                            
                            eval_count = len(evaluations_data) if evaluations_data else 0
                            logger.info(
                                f"[WebSocket] AI analysis result added to response | "
                                f"image_id={image_id} | "
                                f"has_ai_analysis={bool(ai_analysis_text)} | "
                                f"has_evaluations={bool(evaluations_data)} | "
                                f"evaluations_count={eval_count}"
                            )
                        else:
                            base_result["ai_warning"] = ai_result.get("error") or "AI analysis failed"
                            logger.warning(
                                f"[WebSocket] AI analysis failed | "
                                f"image_id={image_id} | "
                                f"error={base_result.get('ai_warning')}"
                            )
                    except Exception as e:
                        base_result["ai_warning"] = str(e)
                        logger.error(
                            f"[WebSocket] AI analysis exception | "
                            f"image_id={image_id} | "
                            f"error={e}",
                            exc_info=True
                        )

                # Log final result structure for debugging
                logger.info(
                    f"[WebSocket] Result structure built | "
                    f"image_id={image_id} | "
                    f"has_quality={bool(base_result.get('quality'))} | "
                    f"has_aesthetic_score={base_result.get('aesthetic_score') is not None} | "
                    f"has_ai_analysis={base_result.get('ai_analysis') is not None} | "
                    f"has_evaluations={base_result.get('evaluations') is not None}"
                )

                analysis_cache.remove_from_section(task_id, image_id)
                analysis_cache.update_image_status(task_id, image_id, "completed", success=True, ai_warning=base_result.get("ai_warning"))
                return {"image_id": image_id, "success": True, "result": base_result}

            executor = ThreadPoolExecutor(max_workers=concurrent_count)
            futures: set = set()
            drain_deadline: Optional[float] = None
            DRAIN_TIMEOUT = 2.0

            while True:
                task_now = analysis_cache.get_task(task_id)
                if not task_now:
                    break

                while len(futures) < concurrent_count:
                    try:
                        image_id = task_now.pending_queue.get_nowait()
                    except queue_module.Empty:
                        break
                    futures.add(executor.submit(analyze_one, image_id))

                done = [f for f in list(futures) if f.done()]
                for f in done:
                    futures.remove(f)
                    try:
                        r = f.result()
                        image_id = int(r.get("image_id"))
                        task_latest = analysis_cache.get_task(task_id)
                        if not task_latest:
                            continue
                        processed = task_latest.success_count + task_latest.fail_count
                        if r.get("success"):
                            result_data = r.get("result", {})
                            logger.info(
                                f"[WebSocket] Preparing completion message | "
                                f"image_id={image_id} | "
                                f"has_result={bool(result_data)} | "
                                f"has_quality={bool(result_data.get('quality'))} | "
                                f"has_ai_analysis={bool(result_data.get('ai_analysis'))} | "
                                f"has_evaluations={bool(result_data.get('evaluations'))}"
                            )
                            _emit_progress(
                                socketio,
                                analysis_room,
                                image_id,
                                processed,
                                task_latest.total,
                                task_latest.success_count,
                                task_latest.fail_count,
                                "completed",
                                result=result_data,
                                task_id=task_id,
                            )
                        else:
                            _emit_progress(
                                socketio,
                                analysis_room,
                                image_id,
                                processed,
                                task_latest.total,
                                task_latest.success_count,
                                task_latest.fail_count,
                                "error",
                                error=r.get("error"),
                                task_id=task_id,
                            )
                    except Exception as e:
                        logger.error(f"[WebSocket] Task future error: {e}", exc_info=True)

                task_now = analysis_cache.get_task(task_id)
                if not task_now:
                    break

                pending_empty = task_now.pending_queue.empty()
                section_empty = analysis_cache.get_section_size(task_id) == 0
                futures_empty = len(futures) == 0

                if pending_empty and section_empty and futures_empty:
                    if drain_deadline is None:
                        drain_deadline = time.time() + DRAIN_TIMEOUT
                    elif time.time() >= drain_deadline:
                        analysis_cache.complete_task(task_id)
                        cached_statuses = analysis_cache.get_all_image_statuses(task_id)
                        section = analysis_cache.get_section(task_id)
                        complete_message = create_analysis_complete_message(
                            total=task_now.total,
                            success_count=task_now.success_count,
                            fail_count=task_now.fail_count,
                            task_id=task_id,
                            image_statuses=cached_statuses,
                            section=section,
                        )
                        socketio.emit("analysis_complete", complete_message, room=analysis_room)
                        socketio.emit(
                            "batch_update",
                            create_unified_message(
                                type="image_analysis",
                                code=MessageCode.ANALYSIS_COMPLETE,
                                message="Batch analysis completed",
                                data={
                                    "batch_id": task_id,
                                    "status": "completed",
                                    "total": task_now.total,
                                    "success_count": task_now.success_count,
                                    "failed_count": task_now.fail_count,
                                    "batch_status": {
                                        "pending_count": 0,
                                        "running_count": 0,
                                        "completed_count": task_now.success_count,
                                        "failed_count": task_now.fail_count,
                                        "total": task_now.total,
                                    },
                                    "tasks": cached_statuses or [],
                                },
                            ),
                            room=analysis_room,
                        )
                        break
                else:
                    drain_deadline = None

                time.sleep(0.1)

        except Exception as e:
            logger.error(f"[WebSocket] Batch worker failed: {e}", exc_info=True)
            analysis_cache.complete_task(task_id, error=str(e))
            socketio.emit("analysis_error", create_analysis_error_message(str(e)), room=analysis_room)
            socketio.emit(
                "batch_update",
                create_unified_message(
                    type="image_analysis",
                    code=MessageCode.ANALYSIS_ERROR,
                    message="Batch analysis error",
                    data={
                        "batch_id": task_id,
                        "status": "failed",
                        "error": str(e),
                        "error_code": "BATCH_PROCESSING_ERROR",
                    },
                ),
                room=analysis_room,
            )

    threading.Thread(target=_worker, daemon=True).start()
    return task_id


def register_analysis_events(socketio):
    """注册分析相关 WebSocket 事件"""
    logger = get_logger()

    @socketio.on("connect")
    def handle_connect():
        logger.info(f"[WebSocket] Client connected | sid={request.sid}")
        emit("connected", {"message": "Connected successfully"})

    @socketio.on("disconnect")
    def handle_disconnect():
        sid = request.sid
        logger.info(f"[WebSocket] Client disconnected | sid={sid}")

    @socketio.on("join_analysis")
    def handle_join_analysis(data):
        """
        加入分析房间。图片分析仅追加、单一会话，使用稳定 client_id 对应唯一房间；
        刷新后重连复用同房间，可继续接收进度。
        """
        client_id = (data or {}).get("client_id") or ""
        client_id = (client_id or "").strip()
        if not client_id:
            logger.warning("[WebSocket] Missing client_id in join_analysis request")
            return
        room = f"analysis_{client_id}"
        join_room(room)
        logger.info(f"[WebSocket] Joined analysis room | room={room} | sid={request.sid}")

    @socketio.on("heartbeat")
    def handle_heartbeat(request_data):
        """
        Heartbeat request (client -> server).

        Client payload format:
        {
          "type": "image_analysis",
          "data": { "batch_id": "...", "timestamp": 1700000000000 }
        }
        """
        try:
            payload = request_data or {}
            req_type = (payload.get("type") or "").strip()
            data = payload.get("data") or {}
            if req_type != "image_analysis":
                msg = create_unified_message(
                    type="image_analysis",
                    code=MessageCode.ERROR,
                    message=f"Unsupported business type: {req_type or '(empty)'}",
                    data={"error": "INVALID_TYPE"},
                )
                emit("batch_update", msg)
                return

            batch_id = (data.get("batch_id") or "").strip() or None
            # If batch_id not provided, try get current active task by client_id
            if not batch_id:
                # Prefer stable client_id stored in room name; client should always provide batch_id.
                # Fallback: use sid-scoped guess: not available; return not found.
                msg = create_unified_message(
                    type="image_analysis",
                    code=MessageCode.BATCH_NOT_FOUND,
                    message="Batch not found or cleaned up",
                    data={"batch_id": None, "batch_exists": False, "reason": "batch_id is required"},
                )
                emit("batch_update", msg)
                return

            task = analysis_cache.get_task(batch_id)
            if not task:
                msg = create_unified_message(
                    type="image_analysis",
                    code=MessageCode.BATCH_NOT_FOUND,
                    message="Batch not found or cleaned up",
                    data={
                        "batch_id": batch_id,
                        "batch_exists": False,
                        "reason": "batch_id not found",
                    },
                )
                emit("batch_update", msg)
                return

            batch_status = {
                "status": "completed" if task.is_complete else "running",
                "pending_count": task.pending_queue.qsize(),
                "running_count": len(task.section),
                "completed_count": task.success_count,
                "failed_count": task.fail_count,
                "total": task.total,
            }
            if task.is_complete:
                msg = create_unified_message(
                    type="image_analysis",
                    code=MessageCode.HEARTBEAT_RESPONSE,
                    message="Batch completed",
                    data={"batch_id": batch_id, "batch_exists": True, "batch_status": batch_status},
                )
            else:
                msg = create_unified_message(
                    type="image_analysis",
                    code=MessageCode.BATCH_STILL_RUNNING,
                    message="Batch status query successful",
                    data={"batch_id": batch_id, "batch_exists": True, "batch_status": batch_status},
                )
            emit("batch_update", msg)
        except Exception as e:
            logger.error(f"[WebSocket] Heartbeat failed: {e}", exc_info=True)
            msg = create_unified_message(
                type="image_analysis",
                code=MessageCode.ERROR,
                message="Heartbeat failed",
                data={"error": str(e)},
            )
            emit("batch_update", msg)

    @socketio.on("start_analysis")
    def handle_start_analysis(data):
        payload = data or {}
        image_ids = payload.get("image_ids") or []
        settings = payload.get("settings") or {}
        client_id = (payload.get("client_id") or "").strip()

        logger.info(
            f"[WebSocket] Analysis request received | "
            f"sid={request.sid} | "
            f"client_id={client_id or '(none)'} | "
            f"image_count={len(image_ids)}"
        )
        logger.debug(f"[WebSocket] Analysis settings | settings={settings}")
        logger.debug(
            f"[WebSocket] Evaluation questions | "
            f"count={len(settings.get('evaluation_questions', []))}"
        )

        if not image_ids:
            error_message = create_analysis_error_message("Image ID list is empty")
            emit("analysis_error", error_message)
            logger.warning("[WebSocket] Image ID list is empty")
            return

        if not client_id:
            error_message = create_analysis_error_message(
                "Missing client_id, please connect and join_analysis first"
            )
            emit("analysis_error", error_message)
            logger.warning("[WebSocket] Missing client_id in start_analysis request")
            return

        try:
            analysis_room = f"analysis_{client_id}"
            join_room(analysis_room)
            
            # 检查是否有进行中的批次（同一 client_id 只能有一个活跃批次）
            existing_task = analysis_cache.get_task_by_session(client_id)
            if existing_task:
                # 追加到现有批次（后端会自动去重）
                original_count = len(image_ids)
                appended_task_id = analysis_cache.append_images(client_id, image_ids)
                if appended_task_id:
                    task = analysis_cache.get_task(appended_task_id)
                    section = analysis_cache.get_section(appended_task_id) if appended_task_id else None
                    
                    # 计算实际追加的数量（去重后）
                    # appended_images 返回的 task.total 是追加后的总数
                    # 实际追加数量 = 新总数 - 旧总数
                    old_total = len(existing_task.image_ids)
                    new_total = task.total if task else old_total
                    actually_appended = new_total - old_total
                    
                    appended_message = create_analysis_appended_message(
                        task_id=appended_task_id,
                        appended_count=actually_appended,
                        new_total=new_total,
                        section=section
                    )
                    socketio.emit("analysis_appended", appended_message, room=analysis_room)
                    logger.info(
                        f"[WebSocket] Images appended to existing batch | "
                        f"task_id={appended_task_id} | "
                        f"requested={original_count} | "
                        f"appended={actually_appended} | "
                        f"old_total={old_total} | "
                        f"new_total={new_total}"
                    )
                    return
                else:
                    logger.warning(
                        "[WebSocket] Append failed (all images may already be in batch), creating new batch"
                    )
            
            # Create and start a new batch
            task_id = start_analysis_batch(
                socketio=socketio,
                client_id=client_id,
                image_ids=image_ids,
                settings=settings,
            )
            logger.info(
                "[WebSocket] Analysis batch started: task_id=%s, client_id=%s, total=%s",
                task_id, client_id, len(image_ids),
            )
            return

        except Exception as e:
            logger.exception("[WebSocket] 启动分析失败: %s", e)
            # 使用标准化消息格式
            error_message = create_analysis_error_message(str(e))
            emit("analysis_error", error_message)
            # v2 unified push (batch_update)
            try:
                socketio.emit(
                    "batch_update",
                    create_unified_message(
                        type="image_analysis",
                        code=MessageCode.ANALYSIS_ERROR,
                        message="Batch analysis error",
                        data={
                            "batch_id": None,
                            "status": "failed",
                            "error": str(e),
                            "error_code": "BATCH_PROCESSING_ERROR",
                        },
                    ),
                    room=f"analysis_{client_id}" if client_id else None,
                )
            except Exception:
                pass
            return

            # LEGACY_WORKER_BLOCK_REMOVED
            # The old inline worker implementation is kept here only for reference during refactor.
            # It is disabled to avoid unreachable / duplicated logic.
            # 
            # def analyze_task():
            #     """
            #     批次化分析任务 worker(从 pending_queue 循环取任务, 维护 section)
            #     完成条件: pending 空 + section 空 + 等待 2 秒确认无新追加
            #     """
            #     import time
            #                 import queue as queue_module
            # 
                            # 从任务缓存获取任务和设置
            #                 task = analysis_cache.get_task(task_id)
            #                 if not task:
            #                     logger.error(f"[WebSocket] 任务不存在: task_id={task_id}")
            #                     return
            # 
            #                 task_settings = task.settings
            #                 evaluation_questions = list(
            #                     task_settings.get("evaluation_questions") or []
            #                 )
            #                 aesthetic_mode = task_settings.get("aesthetic_mode", "none")
                            # CLIP 模式不支持自定义评估问题，一律清空
            #                 if aesthetic_mode == "clip":
            #                     evaluation_questions = []
            #                     logger.debug(
            #                         "[WebSocket] aesthetic_mode=clip，已忽略 evaluation_questions"
            #                     )
            #                 concurrent_count = task_settings.get("concurrentCount", 1)
            #                 concurrent_count = max(1, min(10, int(concurrent_count)))
            #                 write_xmp = task_settings.get("write_xmp", True)
            # 
            #                 logger.info(
            #                     f"[WebSocket] 批次 worker 启动: task_id={task_id}, "
            #                     f"aesthetic_mode={aesthetic_mode}, concurrent={concurrent_count}, pending={task.pending_queue.qsize()}"
            #                 )
            # 
                            # 根据 settings 创建 AI 分析器（只有 AI 模式或需要评估问题时才创建）
                            # 注意：evaluation_questions 需要 AI 分析器，所以也创建
            #                 ai_analyzer = None
            #                 if aesthetic_mode == "ai" or evaluation_questions:
            #                     from services.service_factory import ServiceFactory
            #                     ai_analyzer = ServiceFactory.create_ai_analyzer(
            #                         model=task_settings.get("ai_model", "ollama"),
            #                         api_key=task_settings.get("ai_api_key"),
            #                         ollama_base_url=task_settings.get("ollama_base_url", "http://localhost:11434"),
            #                         ollama_model=task_settings.get("ollama_model", "llama3.2-vision")
            #                     )
            #                     logger.debug(
            #                         f"[WebSocket] 已创建 AI 分析器: model={task_settings.get('ai_model', 'ollama')}, "
            #                         f"aesthetic_mode={aesthetic_mode}, has_evaluation_questions={len(evaluation_questions) > 0}"
            #                     )
            # 
                            # 定义单个图片的分析函数
                            # def analyze_single_image(image_id: int):
                            #     """
                            #     分析单张图片(每个线程使用独立的数据库连接)
                            #     维护 section: 开始分析时加入, 完成/失败时移除
                            #     """
                                # 每个线程使用独立的数据库连接，确保线程安全
            #                     thread_db = get_db()
            #                     thread_image_repo = ImageRepository(thread_db)
            #                     thread_image_service = ImageService(
            #                         aesthetic_mode=aesthetic_mode,
            #                         ai_analyzer=ai_analyzer
            #                     )
            # 
                                # 开始分析：加入 section，更新状态，通知前端
            #                     analysis_cache.add_to_section(task_id, image_id)
            #                     analysis_cache.update_image_status(task_id, image_id, "analyzing", success=False)
            # 
                                # 获取当前任务状态用于进度显示
            #                     task = analysis_cache.get_task(task_id)
            #                     if task:
            #                         processed = task.success_count + task.fail_count
            #                         _emit_progress(
            #                             socketio, analysis_room, image_id,
            #                             processed, task.total,
            #                             task.success_count, task.fail_count,
            #                             "analyzing", task_id=task_id
            #                         )
            #                         logger.info(
            #                             f"[WebSocket] 开始分析图片: image_id={image_id}, "
            #                             f"processed={processed}/{task.total}, section_size={analysis_cache.get_section_size(task_id)}"
            #                         )
            # 
            #                     try:
            #                         image = thread_image_repo.find_by_id(image_id)
            #                         if not image:
            #                             error_msg = "图像不存在"
            #                             logger.warning(f"[WebSocket] 图片不存在: image_id={image_id}")
                                        # 从 section 移除，更新状态，通知前端
            #                             analysis_cache.remove_from_section(task_id, image_id)
            #                             analysis_cache.update_image_status(task_id, image_id, "error", success=False, error=error_msg)
            #                             task = analysis_cache.get_task(task_id)
            #                             if task:
            #                                 _emit_progress(
            #                                     socketio, analysis_room, image_id,
            #                                     task.success_count + task.fail_count, task.total,
            #                                     task.success_count, task.fail_count,
            #                                     "error", error=error_msg, task_id=task_id
            #                                 )
            #                             return {
            #                                 "image_id": image_id,
            #                                 "success": False,
            #                                 "error": error_msg
            #                             }
            # 
                                    # 执行基础质量分析
            #                         result = thread_image_service.process_image(image.file_path, write_xmp=write_xmp)
            # 
                                    # 只有 AI 模式时才执行 AI 深度分析（描述、评估、自定义问题等）
                                    # evaluation_questions 需要 AI 分析，所以如果有评估问题，也执行 AI 分析
            #                         ai_error_message = None
            #                         ai_analysis_data = None
            #                         if (aesthetic_mode == "ai" or evaluation_questions) and ai_analyzer:
            #                             try:
            #                                 logger.info(f"[WebSocket] 开始AI分析: image_id={image_id}, file_path={image.file_path}")
            #                                 logger.info(f"[WebSocket] 评估问题: {evaluation_questions}")
            # 
            #                                 ai_result = ai_analyzer.analyze_image(
            #                                     image.file_path,
            #                                     evaluation_questions=evaluation_questions
            #                                 )
            # 
            #                                 logger.info(f"[WebSocket] AI分析结果: image_id={image_id}, success={ai_result.get('success')}")
            #                                 logger.info(f"[WebSocket] AI分析响应: {ai_result}")
            # 
            #                                 if ai_result.get("success"):
                                                # 保存 AI 分析结果和评估结果到数据库
            #                                     from repositories.metadata_repository import MetadataRepository
            #                                     import json
            #                                     metadata_repo = MetadataRepository(thread_db)
            #                                     metadata = metadata_repo.find_by_image_id(image_id)
            # 
            #                                     ai_analysis_text = ai_result.get("analysis", "")
            #                                     evaluations = ai_result.get("evaluations", [])
            # 
            #                                     logger.info(f"[WebSocket] AI分析文本长度: {len(str(ai_analysis_text)) if ai_analysis_text else 0}")
            #                                     logger.info(f"[WebSocket] 评估结果数量: {len(evaluations) if evaluations else 0}")
            #                                     logger.info(f"[WebSocket] 评估结果详情: {evaluations}")
            # 
                                                # 准备WebSocket推送的数据
            #                                     ai_analysis_data = {
            #                                         'ai_analysis': ai_analysis_text,
            #                                         'evaluations': evaluations
            #                                     }
            # 
            #                                     if metadata:
                                                    # 更新 AI 分析结果和评估结果
            #                                         if ai_analysis_text:
                                                        # 如果 analysis 是字符串，直接使用；如果是字典，转换为 JSON
            #                                             if isinstance(ai_analysis_text, dict):
            #                                                 metadata.ai_analysis = json.dumps(ai_analysis_text, ensure_ascii=False)
            #                                             else:
            #                                                 metadata.ai_analysis = str(ai_analysis_text)
            # 
            #                                         if evaluations:
            #                                             metadata.evaluations = json.dumps(evaluations, ensure_ascii=False)
            # 
            #                                         metadata_repo.update(metadata)
            #                                         logger.info(f"[WebSocket] AI分析结果已保存到数据库: image_id={image_id}")
            #                                         logger.info(f"[WebSocket] 保存的ai_analysis长度: {len(metadata.ai_analysis) if metadata.ai_analysis else 0}")
            #                                         logger.info(f"[WebSocket] 保存的evaluations: {metadata.evaluations}")
            #                                     else:
                                                    # 如果元数据不存在，创建新的
            #                                         xmp_data = {
            #                                             'ai_analysis': json.dumps(ai_analysis_text, ensure_ascii=False) if isinstance(ai_analysis_text, dict) else str(ai_analysis_text) if ai_analysis_text else None,
            #                                             'evaluations': json.dumps(evaluations, ensure_ascii=False) if evaluations else None
            #                                         }
            #                                         metadata_repo.create_or_update(image_id, xmp_data)
            #                                         logger.info(f"[WebSocket] 创建新元数据并保存AI分析结果: image_id={image_id}")
            #                                 else:
                                                # AI分析失败，记录错误信息并反馈给前端
            #                                     ai_error_message = ai_result.get("error", "AI分析失败")
            #                                     logger.warning(f"[WebSocket] AI分析失败: image_id={image_id}, error={ai_error_message}")
            #                             except Exception as ai_error:
                                            # AI分析异常，记录错误信息并反馈给前端
            #                                 ai_error_message = f"AI分析异常: {str(ai_error)}"
            #                                 logger.exception(f"[WebSocket] AI分析异常: image_id={image_id}, error={ai_error}")
            # 
            #                         if result.get("success"):
                                        # 如果基础分析成功，但AI分析失败，在结果中包含警告信息
            #                             progress_result = result.copy()
            #                             if ai_error_message:
            #                                 progress_result["ai_warning"] = ai_error_message
                                        # 如果AI分析成功，将AI分析结果也包含在WebSocket消息中
            #                             if ai_analysis_data:
            #                                 progress_result["ai_analysis"] = ai_analysis_data.get("ai_analysis")
            #                                 progress_result["evaluations"] = ai_analysis_data.get("evaluations")
            #                                 logger.info(f"[WebSocket] 通过WebSocket推送AI分析结果: image_id={image_id}, has_ai_analysis={bool(ai_analysis_data.get('ai_analysis'))}, evaluations_count={len(ai_analysis_data.get('evaluations', []))}")
            # 
                                        # 确保返回结果包含所有必要字段
            #                             return {
            #                                 "image_id": image_id,
            #                                 "success": True,
            #                                 "result": progress_result,  # 即使没有 AI 分析，也包含基础分析结果
            #                                 "ai_error": ai_error_message
            #                             }
            #                         else:
            #                             error_msg = result.get("error", "分析失败")
                                        # 如果同时有AI分析错误，合并错误信息
            #                             if ai_error_message:
            #                                 error_msg = f"{error_msg}；AI分析错误: {ai_error_message}"
            #                             return {
            #                                 "image_id": image_id,
            #                                 "success": False,
            #                                 "error": error_msg
            #                             }
            # 
            #                     except Exception as e:
            #                         logger.exception("[WebSocket] 分析失败: image_id=%s", image_id)
            #                         error_msg = str(e)
                                    # 从 section 移除，更新状态，通知前端
            #                         analysis_cache.remove_from_section(task_id, image_id)
            #                         analysis_cache.update_image_status(task_id, image_id, "error", success=False, error=error_msg)
            #                         task = analysis_cache.get_task(task_id)
            #                         if task:
            #                             _emit_progress(
            #                                 socketio, analysis_room, image_id,
            #                                 task.success_count + task.fail_count, task.total,
            #                                 task.success_count, task.fail_count,
            #                                 "error", error=error_msg, task_id=task_id
            #                             )
            #                         return {
            #                             "image_id": image_id,
            #                             "success": False,
            #                             "error": error_msg
            #                         }
            # 
            #                 try:
                                # 使用线程池实现并发控制（长期运行，支持动态添加任务）
            #                     with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
            #                         futures: Dict[Any, int] = {}  # future -> image_id
            #                         drain_deadline: Optional[float] = None  # 首次 pending 空时开始计时
            #                         DRAIN_TIMEOUT = 2.0  # 等待新追加的超时时间（秒）
            # 
            #                         while True:
                                        # 1. 从 pending_queue 取任务并提交（直到达到并发上限）
            #                             while len(futures) < concurrent_count:
            #                                 image_id = analysis_cache.get_next_pending(task_id, timeout=0.1)
            #                                 if image_id is None:
            #                                     break  # 队列暂时为空
            # 
                                            # 双重检查：确保图片不在 section 中（防止重复分析）
            #                                 task = analysis_cache.get_task(task_id)
            #                                 if task:
            #                                     section_ids = {item.id for item in task.section}
            #                                     if image_id in section_ids:
            #                                         logger.warning(
            #                                             f"[WebSocket] 检测到重复分析请求，跳过: image_id={image_id}, "
            #                                             f"已在 section 中"
            #                                         )
            #                                         continue
            # 
                                            # 提交到线程池
            #                                 future = executor.submit(analyze_single_image, image_id)
            #                                 futures[future] = image_id
            #                                 logger.debug(
            #                                     f"[WebSocket] 提交分析任务: image_id={image_id}, "
            #                                     f"in_flight={len(futures)}, concurrent={concurrent_count}"
            #                                 )
            # 
                                        # 2. 处理已完成的任务
            #                             done_futures = [f for f in futures if f.done()]
            #                             for future in done_futures:
            #                                 image_id = futures.pop(future)
            # 
            #                                 try:
            #                                     result = future.result()
            #                                     task = analysis_cache.get_task(task_id)
            #                                     if not task:
            #                                         logger.warning(f"[WebSocket] 任务已不存在: task_id={task_id}")
            #                                         continue
            # 
            #                                     if result["success"]:
            #                                         progress_result = result.get("result", {})
            #                                         ai_warning = result.get("ai_error")
            # 
                                                    # 从 section 移除（正常完成），更新状态
            #                                         analysis_cache.remove_from_section(task_id, image_id)
            #                                         analysis_cache.update_image_status(
            #                                             task_id, image_id, "completed",
            #                                             success=True, ai_warning=ai_warning
            #                                         )
            # 
                                                    # 发送完成状态
            #                                         processed = task.success_count + task.fail_count
            #                                         _emit_progress(
            #                                             socketio, analysis_room, image_id,
            #                                             processed, task.total,
            #                                             task.success_count, task.fail_count,
            #                                             "completed", result=progress_result, task_id=task_id
            #                                         )
            #                                         logger.info(
            #                                             f"[WebSocket] 图片分析完成: image_id={image_id}, "
            #                                             f"processed={processed}/{task.total}, section_size={analysis_cache.get_section_size(task_id)}"
            #                                         )
            #                                     else:
            #                                         error_msg = result.get("error", "分析失败")
            # 
                                                    # 从 section 移除（失败），更新状态
                                                    # 注意：如果 analyze_single_image 中已移除（如 image 不存在），这里会安全地忽略
            #                                         analysis_cache.remove_from_section(task_id, image_id)
            #                                         analysis_cache.update_image_status(
            #                                             task_id, image_id, "error",
            #                                             success=False, error=error_msg
            #                                         )
            # 
                                                    # 发送错误状态
            #                                         task = analysis_cache.get_task(task_id)
            #                                         if task:
            #                                             processed = task.success_count + task.fail_count
            #                                             _emit_progress(
            #                                                 socketio, analysis_room, image_id,
            #                                                 processed, task.total,
            #                                                 task.success_count, task.fail_count,
            #                                                 "error", error=error_msg, task_id=task_id
            #                                             )
            #                                         logger.warning(
            #                                             f"[WebSocket] 图片分析失败: image_id={image_id}, error={error_msg}"
            #                                         )
            #                                 except Exception as e:
            #                                     logger.exception(f"[WebSocket] 处理结果异常: image_id={image_id}")
                                                # 从 section 移除（异常情况，确保清理）
                                                # 注意：如果 analyze_single_image 中已移除，这里会安全地忽略
            #                                     analysis_cache.remove_from_section(task_id, image_id)
            # 
                                        # 3. 检查完成条件：pending 空 + section 空
            #                             task = analysis_cache.get_task(task_id)
            #                             if not task:
            #                                 logger.warning(f"[WebSocket] 任务已不存在，退出 worker: task_id={task_id}")
            #                                 break
            # 
            #                             pending_empty = task.pending_queue.empty()
            #                             section_empty = analysis_cache.get_section_size(task_id) == 0
            #                             futures_empty = len(futures) == 0
            # 
            #                             if pending_empty and section_empty and futures_empty:
                                            # 所有任务完成，等待一段时间确认没有新追加
            #                                 if drain_deadline is None:
            #                                     drain_deadline = time.time() + DRAIN_TIMEOUT
            #                                     logger.debug(
            #                                         f"[WebSocket] 开始等待新追加: task_id={task_id}, "
            #                                         f"wait_until={drain_deadline:.2f}"
            #                                     )
            #                                 elif time.time() >= drain_deadline:
                                                # 确认完成：标记任务完成，发送完成消息
            #                                     analysis_cache.complete_task(task_id)
            # 
            #                                     cached_statuses = analysis_cache.get_all_image_statuses(task_id)
            #                                     section = analysis_cache.get_section(task_id)
            #                                     complete_message = create_analysis_complete_message(
            #                                         total=task.total,
            #                                         success_count=task.success_count,
            #                                         fail_count=task.fail_count,
            #                                         task_id=task_id,
            #                                         image_statuses=cached_statuses,
            #                                         section=section
            #                                     )
            #                                     socketio.emit("analysis_complete", complete_message, room=analysis_room)
                                                # v2 unified push (batch_update) - completion double guarantee
            #                                     try:
            #                                         socketio.emit(
            #                                             "batch_update",
            #                                             create_unified_message(
            #                                                 type="image_analysis",
            #                                                 code=MessageCode.ANALYSIS_COMPLETE,
            #                                                 message="Batch analysis completed",
            #                                                 data={
            #                                                     "batch_id": task_id,
            #                                                     "status": "completed",
            #                                                     "total": task.total,
            #                                                     "success_count": task.success_count,
            #                                                     "failed_count": task.fail_count,
            #                                                     "batch_status": {
            #                                                         "pending_count": 0,
            #                                                         "running_count": 0,
            #                                                         "completed_count": task.success_count,
            #                                                         "failed_count": task.fail_count,
            #                                                         "total": task.total,
            #                                                     },
            #                                                     "tasks": cached_statuses or [],
            #                                                 },
            #                                             ),
            #                                             room=analysis_room,
            #                                         )
            #                                     except Exception:
            #                                         pass
            # 
            #                                     logger.info(
            #                                         f"[WebSocket] 批次完成: task_id={task_id}, "
            #                                         f"success={task.success_count}, failed={task.fail_count}, "
            #                                         f"total={task.total}"
            #                                     )
            #                                     break
            #                             else:
                                            # 有新任务或正在处理，重置完成计时
            #                                 drain_deadline = None
            # 
                                        # 短暂休眠，避免 CPU 占用过高
            #                             time.sleep(0.1)
            # 
            #                 except Exception as e:
            #                     logger.exception("[WebSocket] 分析任务异常: %s", e)
            #                     error_msg = str(e)
                                # 标记任务失败
            #                     analysis_cache.complete_task(task_id, error=error_msg)
                                # 使用标准化消息格式
            #                     error_message = create_analysis_error_message(error_msg)
            #                     socketio.emit("analysis_error", error_message, room=analysis_room)

            #     t = threading.Thread(target=analyze_task, daemon=True)
            #     t.start()


def _emit_progress(socketio, room, image_id, current, total, success, failed, status, result=None, error=None, task_id=None):
    """
    发送分析进度消息(标准化格式)
    
    Args:
        socketio: SocketIO 实例
        room: 分析房间名(analysis_{client_id}), 单一会话仅追加图片
        image_id: 图片ID
        current: 当前处理的图片序号
        total: 总图片数
        success: 成功数量
        failed: 失败数量
        status: 状态('pending', 'analyzing', 'completed', 'error')
        result: 分析结果(可选)
        error: 错误信息(可选)
        task_id: 任务ID(可选, 用于获取 section 信息)
    """
    logger = get_logger()
    
    # 获取 section 信息（如果提供了 task_id）
    section = None
    if task_id:
        section = analysis_cache.get_section(task_id)
    
    # 使用标准化消息格式
    message = create_analysis_progress_message(
        image_id=image_id,
        current=current,
        total=total,
        success=success,
        failed=failed,
        status=status,
        result=result,
        error=error,
        section=section,
        task_id=task_id  # 包含任务ID，用于前端区分不同批次
    )
    
    # Log progress message being sent
    logger.info(
        f"[WebSocket] Sending analysis progress | "
        f"image_id={image_id} | "
        f"status={status} | "
        f"progress={current}/{total} | "
        f"has_result={result is not None} | "
        f"section_size={len(section) if section else 0}"
    )
    
    socketio.emit("analysis_progress", message, room=room)

    # v2 unified push (batch_update)
    try:
        # Prefer authoritative counts from cache when available
        task = analysis_cache.get_task(task_id) if task_id else None
        if task:
            batch_status = {
                "pending_count": task.pending_queue.qsize(),
                "running_count": len(task.section),
                "completed_count": task.success_count,
                "failed_count": task.fail_count,
                "total": task.total,
            }
        else:
            batch_status = {
                "pending_count": max(0, int(total) - int(success) - int(failed)),
                "running_count": 1 if status == "analyzing" else 0,
                "completed_count": int(success),
                "failed_count": int(failed),
                "total": int(total),
            }

        if status == "analyzing":
            socketio.emit(
                "batch_update",
                create_unified_message(
                    type="image_analysis",
                    code=MessageCode.ANALYSIS_PROGRESS,
                    message="Task progress updated",
                    data={
                        "batch_id": task_id,
                        "image_id": image_id,
                        "status": "running",
                        "progress": 0.0,
                        "batch_status": batch_status,
                    },
                ),
                room=room,
            )
        elif status == "completed":
            socketio.emit(
                "batch_update",
                create_unified_message(
                    type="image_analysis",
                    code=MessageCode.ANALYSIS_TASK_UPDATE,
                    message="Task analysis completed",
                    data={
                        "batch_id": task_id,
                        "image_id": image_id,
                        "status": "completed",
                        "progress": 100.0,
                        "result": result or {},
                        "batch_status": batch_status,
                    },
                ),
                room=room,
            )
        elif status == "error":
            socketio.emit(
                "batch_update",
                create_unified_message(
                    type="image_analysis",
                    code=MessageCode.ANALYSIS_TASK_UPDATE,
                    message="Task analysis failed",
                    data={
                        "batch_id": task_id,
                        "image_id": image_id,
                        "status": "failed",
                        "progress": 0.0,
                        "error": error or "Unknown error",
                        "error_code": "TASK_FAILED",
                        "batch_status": batch_status,
                    },
                ),
                room=room,
            )
    except Exception:
        # Never break legacy progress push
        pass

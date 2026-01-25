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


def register_analysis_events(socketio):
    """注册分析相关 WebSocket 事件"""
    logger = get_logger()

    @socketio.on("connect")
    def handle_connect():
        logger.info("[WebSocket] 客户端连接: %s", request.sid)
        emit("connected", {"message": "连接成功"})

    @socketio.on("disconnect")
    def handle_disconnect():
        sid = request.sid
        logger.info("[WebSocket] 客户端断开: %s", sid)

    @socketio.on("join_analysis")
    def handle_join_analysis(data):
        """
        加入分析房间。图片分析仅追加、单一会话，使用稳定 client_id 对应唯一房间；
        刷新后重连复用同房间，可继续接收进度。
        """
        client_id = (data or {}).get("client_id") or ""
        client_id = (client_id or "").strip()
        if not client_id:
            logger.warning("[WebSocket] join_analysis 缺少 client_id")
            return
        room = f"analysis_{client_id}"
        join_room(room)
        logger.info("[WebSocket] 已加入分析房间: room=%s, sid=%s", room, request.sid)

    @socketio.on("start_analysis")
    def handle_start_analysis(data):
        payload = data or {}
        image_ids = payload.get("image_ids") or []
        settings = payload.get("settings") or {}
        client_id = (payload.get("client_id") or "").strip()

        logger.info(
            "[WebSocket] 收到分析请求: sid=%s, client_id=%s, image_ids=%s",
            request.sid, client_id or "(none)", image_ids,
        )
        logger.info("[WebSocket] 分析设置: %s", settings)
        logger.info("[WebSocket] 评估问题: %s", settings.get("evaluation_questions", []))

        if not image_ids:
            error_message = create_analysis_error_message("图像ID列表为空")
            emit("analysis_error", error_message)
            logger.warning("[WebSocket] 图像ID列表为空")
            return

        if not client_id:
            error_message = create_analysis_error_message("缺少 client_id，请先连接并 join_analysis")
            emit("analysis_error", error_message)
            logger.warning("[WebSocket] start_analysis 缺少 client_id")
            return

        try:
            analysis_room = f"analysis_{client_id}"
            join_room(analysis_room)
            
            # 检查是否有进行中的批次
            existing_task = analysis_cache.get_task_by_session(client_id)
            if existing_task:
                # 追加到现有批次
                appended_task_id = analysis_cache.append_images(client_id, image_ids)
                if appended_task_id:
                    task = analysis_cache.get_task(appended_task_id)
                    section = analysis_cache.get_section(appended_task_id) if appended_task_id else None
                    appended_message = create_analysis_appended_message(
                        task_id=appended_task_id,
                        appended_count=len(image_ids),
                        new_total=task.total if task else len(image_ids),
                        section=section
                    )
                    socketio.emit("analysis_appended", appended_message, room=analysis_room)
                    logger.info(
                        "[WebSocket] 追加图片到现有批次: task_id=%s, appended=%s, new_total=%s",
                        appended_task_id, len(image_ids), task.total if task else len(image_ids)
                    )
                    return
                else:
                    logger.warning("[WebSocket] 追加失败，将创建新批次")
            
            # 创建新批次
            task_id = analysis_cache.create_task(client_id, image_ids, settings)
            logger.info(
                "[WebSocket] 创建分析任务: task_id=%s, client_id=%s, room=%s, total=%s",
                task_id, client_id, analysis_room, len(image_ids),
            )

            section = analysis_cache.get_section(task_id)
            started_message = create_analysis_started_message(len(image_ids), task_id, section=section)
            emit("analysis_started", started_message)

            def analyze_task():
                """
                批次化分析任务 worker（从 pending_queue 循环取任务，维护 section）
                完成条件：pending 空 + section 空 + 等待 2 秒确认无新追加
                """
                import time
                import queue as queue_module
                
                # 从任务缓存获取任务和设置
                task = analysis_cache.get_task(task_id)
                if not task:
                    logger.error(f"[WebSocket] 任务不存在: task_id={task_id}")
                    return
                
                task_settings = task.settings
                use_ai = task_settings.get("use_ai", False)
                evaluation_questions = task_settings.get("evaluation_questions", [])
                aesthetic_mode = task_settings.get("aesthetic_mode", "none")
                concurrent_count = task_settings.get("concurrentCount", 1)
                concurrent_count = max(1, min(10, int(concurrent_count)))
                write_xmp = task_settings.get("write_xmp", True)
                
                logger.info(
                    f"[WebSocket] 批次 worker 启动: task_id={task_id}, "
                    f"concurrent={concurrent_count}, pending={task.pending_queue.qsize()}"
                )
                
                # 根据 settings 创建 AI 分析器（如果需要）
                ai_analyzer = None
                if use_ai or evaluation_questions or aesthetic_mode == "ai":
                    from services.service_factory import ServiceFactory
                    ai_analyzer = ServiceFactory.create_ai_analyzer(
                        model=task_settings.get("ai_model", "ollama"),
                        api_key=task_settings.get("ai_api_key"),
                        ollama_base_url=task_settings.get("ollama_base_url", "http://localhost:11434"),
                        ollama_model=task_settings.get("ollama_model", "llama3.2-vision")
                    )
                
                # 定义单个图片的分析函数
                def analyze_single_image(image_id: int):
                    """
                    分析单张图片（每个线程使用独立的数据库连接）
                    维护 section：开始分析时加入，完成/失败时移除
                    """
                    # 每个线程使用独立的数据库连接，确保线程安全
                    thread_db = get_db()
                    thread_image_repo = ImageRepository(thread_db)
                    thread_image_service = ImageService(
                        aesthetic_mode=aesthetic_mode,
                        ai_analyzer=ai_analyzer
                    )
                    
                    # 开始分析：加入 section，更新状态，通知前端
                    analysis_cache.add_to_section(task_id, image_id)
                    analysis_cache.update_image_status(task_id, image_id, "analyzing", success=False)
                    
                    # 获取当前任务状态用于进度显示
                    task = analysis_cache.get_task(task_id)
                    if task:
                        processed = task.success_count + task.fail_count
                        _emit_progress(
                            socketio, analysis_room, image_id,
                            processed, task.total,
                            task.success_count, task.fail_count,
                            "analyzing", task_id=task_id
                        )
                        logger.info(
                            f"[WebSocket] 开始分析图片: image_id={image_id}, "
                            f"processed={processed}/{task.total}, section_size={analysis_cache.get_section_size(task_id)}"
                        )
                    
                    try:
                        image = thread_image_repo.find_by_id(image_id)
                        if not image:
                            error_msg = "图像不存在"
                            logger.warning(f"[WebSocket] 图片不存在: image_id={image_id}")
                            # 从 section 移除，更新状态，通知前端
                            analysis_cache.remove_from_section(task_id, image_id)
                            analysis_cache.update_image_status(task_id, image_id, "error", success=False, error=error_msg)
                            task = analysis_cache.get_task(task_id)
                            if task:
                                _emit_progress(
                                    socketio, analysis_room, image_id,
                                    task.success_count + task.fail_count, task.total,
                                    task.success_count, task.fail_count,
                                    "error", error=error_msg, task_id=task_id
                                )
                            return {
                                "image_id": image_id,
                                "success": False,
                                "error": error_msg
                            }

                        # 执行基础质量分析
                        result = thread_image_service.process_image(image.file_path, write_xmp=write_xmp)
                        
                        # 如果需要 AI 分析或评估问题，执行 AI 分析
                        ai_error_message = None
                        ai_analysis_data = None
                        if (use_ai or evaluation_questions) and ai_analyzer:
                            try:
                                logger.info(f"[WebSocket] 开始AI分析: image_id={image_id}, file_path={image.file_path}")
                                logger.info(f"[WebSocket] 评估问题: {evaluation_questions}")
                                
                                ai_result = ai_analyzer.analyze_image(
                                    image.file_path,
                                    evaluation_questions=evaluation_questions
                                )
                                
                                logger.info(f"[WebSocket] AI分析结果: image_id={image_id}, success={ai_result.get('success')}")
                                logger.info(f"[WebSocket] AI分析响应: {ai_result}")
                                
                                if ai_result.get("success"):
                                    # 保存 AI 分析结果和评估结果到数据库
                                    from repositories.metadata_repository import MetadataRepository
                                    import json
                                    metadata_repo = MetadataRepository(thread_db)
                                    metadata = metadata_repo.find_by_image_id(image_id)
                                    
                                    ai_analysis_text = ai_result.get("analysis", "")
                                    evaluations = ai_result.get("evaluations", [])
                                    
                                    logger.info(f"[WebSocket] AI分析文本长度: {len(str(ai_analysis_text)) if ai_analysis_text else 0}")
                                    logger.info(f"[WebSocket] 评估结果数量: {len(evaluations) if evaluations else 0}")
                                    logger.info(f"[WebSocket] 评估结果详情: {evaluations}")
                                    
                                    # 准备WebSocket推送的数据
                                    ai_analysis_data = {
                                        'ai_analysis': ai_analysis_text,
                                        'evaluations': evaluations
                                    }
                                    
                                    if metadata:
                                        # 更新 AI 分析结果和评估结果
                                        if ai_analysis_text:
                                            # 如果 analysis 是字符串，直接使用；如果是字典，转换为 JSON
                                            if isinstance(ai_analysis_text, dict):
                                                metadata.ai_analysis = json.dumps(ai_analysis_text, ensure_ascii=False)
                                            else:
                                                metadata.ai_analysis = str(ai_analysis_text)
                                        
                                        if evaluations:
                                            metadata.evaluations = json.dumps(evaluations, ensure_ascii=False)
                                        
                                        metadata_repo.update(metadata)
                                        logger.info(f"[WebSocket] AI分析结果已保存到数据库: image_id={image_id}")
                                        logger.info(f"[WebSocket] 保存的ai_analysis长度: {len(metadata.ai_analysis) if metadata.ai_analysis else 0}")
                                        logger.info(f"[WebSocket] 保存的evaluations: {metadata.evaluations}")
                                    else:
                                        # 如果元数据不存在，创建新的
                                        xmp_data = {
                                            'ai_analysis': json.dumps(ai_analysis_text, ensure_ascii=False) if isinstance(ai_analysis_text, dict) else str(ai_analysis_text) if ai_analysis_text else None,
                                            'evaluations': json.dumps(evaluations, ensure_ascii=False) if evaluations else None
                                        }
                                        metadata_repo.create_or_update(image_id, xmp_data)
                                        logger.info(f"[WebSocket] 创建新元数据并保存AI分析结果: image_id={image_id}")
                                else:
                                    # AI分析失败，记录错误信息并反馈给前端
                                    ai_error_message = ai_result.get("error", "AI分析失败")
                                    logger.warning(f"[WebSocket] AI分析失败: image_id={image_id}, error={ai_error_message}")
                            except Exception as ai_error:
                                # AI分析异常，记录错误信息并反馈给前端
                                ai_error_message = f"AI分析异常: {str(ai_error)}"
                                logger.exception(f"[WebSocket] AI分析异常: image_id={image_id}, error={ai_error}")
                        
                        if result.get("success"):
                            # 如果基础分析成功，但AI分析失败，在结果中包含警告信息
                            progress_result = result.copy()
                            if ai_error_message:
                                progress_result["ai_warning"] = ai_error_message
                            # 如果AI分析成功，将AI分析结果也包含在WebSocket消息中
                            if ai_analysis_data:
                                progress_result["ai_analysis"] = ai_analysis_data.get("ai_analysis")
                                progress_result["evaluations"] = ai_analysis_data.get("evaluations")
                                logger.info(f"[WebSocket] 通过WebSocket推送AI分析结果: image_id={image_id}, has_ai_analysis={bool(ai_analysis_data.get('ai_analysis'))}, evaluations_count={len(ai_analysis_data.get('evaluations', []))}")
                            
                            # 确保返回结果包含所有必要字段
                            return {
                                "image_id": image_id,
                                "success": True,
                                "result": progress_result,  # 即使没有 AI 分析，也包含基础分析结果
                                "ai_error": ai_error_message
                            }
                        else:
                            error_msg = result.get("error", "分析失败")
                            # 如果同时有AI分析错误，合并错误信息
                            if ai_error_message:
                                error_msg = f"{error_msg}；AI分析错误: {ai_error_message}"
                            return {
                                "image_id": image_id,
                                "success": False,
                                "error": error_msg
                            }

                    except Exception as e:
                        logger.exception("[WebSocket] 分析失败: image_id=%s", image_id)
                        error_msg = str(e)
                        # 从 section 移除，更新状态，通知前端
                        analysis_cache.remove_from_section(task_id, image_id)
                        analysis_cache.update_image_status(task_id, image_id, "error", success=False, error=error_msg)
                        task = analysis_cache.get_task(task_id)
                        if task:
                            _emit_progress(
                                socketio, analysis_room, image_id,
                                task.success_count + task.fail_count, task.total,
                                task.success_count, task.fail_count,
                                "error", error=error_msg, task_id=task_id
                            )
                        return {
                            "image_id": image_id,
                            "success": False,
                            "error": error_msg
                        }

                try:
                    # 使用线程池实现并发控制（长期运行，支持动态添加任务）
                    with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
                        futures: Dict[Any, int] = {}  # future -> image_id
                        drain_deadline: Optional[float] = None  # 首次 pending 空时开始计时
                        DRAIN_TIMEOUT = 2.0  # 等待新追加的超时时间（秒）
                        
                        while True:
                            # 1. 从 pending_queue 取任务并提交（直到达到并发上限）
                            while len(futures) < concurrent_count:
                                image_id = analysis_cache.get_next_pending(task_id, timeout=0.1)
                                if image_id is None:
                                    break  # 队列暂时为空
                                
                                # 双重检查：确保图片不在 section 中（防止重复分析）
                                task = analysis_cache.get_task(task_id)
                                if task:
                                    section_ids = {item.id for item in task.section}
                                    if image_id in section_ids:
                                        logger.warning(
                                            f"[WebSocket] 检测到重复分析请求，跳过: image_id={image_id}, "
                                            f"已在 section 中"
                                        )
                                        continue
                                
                                # 提交到线程池
                                future = executor.submit(analyze_single_image, image_id)
                                futures[future] = image_id
                                logger.debug(
                                    f"[WebSocket] 提交分析任务: image_id={image_id}, "
                                    f"in_flight={len(futures)}, concurrent={concurrent_count}"
                                )
                            
                            # 2. 处理已完成的任务
                            done_futures = [f for f in futures if f.done()]
                            for future in done_futures:
                                image_id = futures.pop(future)
                                
                                try:
                                    result = future.result()
                                    task = analysis_cache.get_task(task_id)
                                    if not task:
                                        logger.warning(f"[WebSocket] 任务已不存在: task_id={task_id}")
                                        continue
                                    
                                    if result["success"]:
                                        progress_result = result.get("result", {})
                                        ai_warning = result.get("ai_error")
                                        
                                        # 从 section 移除（正常完成），更新状态
                                        analysis_cache.remove_from_section(task_id, image_id)
                                        analysis_cache.update_image_status(
                                            task_id, image_id, "completed",
                                            success=True, ai_warning=ai_warning
                                        )
                                        
                                        # 发送完成状态
                                        processed = task.success_count + task.fail_count
                                        _emit_progress(
                                            socketio, analysis_room, image_id,
                                            processed, task.total,
                                            task.success_count, task.fail_count,
                                            "completed", result=progress_result, task_id=task_id
                                        )
                                        logger.info(
                                            f"[WebSocket] 图片分析完成: image_id={image_id}, "
                                            f"processed={processed}/{task.total}, section_size={analysis_cache.get_section_size(task_id)}"
                                        )
                                    else:
                                        error_msg = result.get("error", "分析失败")
                                        
                                        # 从 section 移除（失败），更新状态
                                        # 注意：如果 analyze_single_image 中已移除（如 image 不存在），这里会安全地忽略
                                        analysis_cache.remove_from_section(task_id, image_id)
                                        analysis_cache.update_image_status(
                                            task_id, image_id, "error",
                                            success=False, error=error_msg
                                        )
                                        
                                        # 发送错误状态
                                        task = analysis_cache.get_task(task_id)
                                        if task:
                                            processed = task.success_count + task.fail_count
                                            _emit_progress(
                                                socketio, analysis_room, image_id,
                                                processed, task.total,
                                                task.success_count, task.fail_count,
                                                "error", error=error_msg, task_id=task_id
                                            )
                                        logger.warning(
                                            f"[WebSocket] 图片分析失败: image_id={image_id}, error={error_msg}"
                                        )
                                except Exception as e:
                                    logger.exception(f"[WebSocket] 处理结果异常: image_id={image_id}")
                                    # 从 section 移除（异常情况，确保清理）
                                    # 注意：如果 analyze_single_image 中已移除，这里会安全地忽略
                                    analysis_cache.remove_from_section(task_id, image_id)
                            
                            # 3. 检查完成条件：pending 空 + section 空
                            task = analysis_cache.get_task(task_id)
                            if not task:
                                logger.warning(f"[WebSocket] 任务已不存在，退出 worker: task_id={task_id}")
                                break
                            
                            pending_empty = task.pending_queue.empty()
                            section_empty = analysis_cache.get_section_size(task_id) == 0
                            futures_empty = len(futures) == 0
                            
                            if pending_empty and section_empty and futures_empty:
                                # 所有任务完成，等待一段时间确认没有新追加
                                if drain_deadline is None:
                                    drain_deadline = time.time() + DRAIN_TIMEOUT
                                    logger.debug(
                                        f"[WebSocket] 开始等待新追加: task_id={task_id}, "
                                        f"wait_until={drain_deadline:.2f}"
                                    )
                                elif time.time() >= drain_deadline:
                                    # 确认完成：标记任务完成，发送完成消息
                                    analysis_cache.complete_task(task_id)
                                    
                                    cached_statuses = analysis_cache.get_all_image_statuses(task_id)
                                    section = analysis_cache.get_section(task_id)
                                    complete_message = create_analysis_complete_message(
                                        total=task.total,
                                        success_count=task.success_count,
                                        fail_count=task.fail_count,
                                        task_id=task_id,
                                        image_statuses=cached_statuses,
                                        section=section
                                    )
                                    socketio.emit("analysis_complete", complete_message, room=analysis_room)
                                    
                                    logger.info(
                                        f"[WebSocket] 批次完成: task_id={task_id}, "
                                        f"success={task.success_count}, failed={task.fail_count}, "
                                        f"total={task.total}"
                                    )
                                    break
                            else:
                                # 有新任务或正在处理，重置完成计时
                                drain_deadline = None
                            
                            # 短暂休眠，避免 CPU 占用过高
                            time.sleep(0.1)

                except Exception as e:
                    logger.exception("[WebSocket] 分析任务异常: %s", e)
                    error_msg = str(e)
                    # 标记任务失败
                    analysis_cache.complete_task(task_id, error=error_msg)
                    # 使用标准化消息格式
                    error_message = create_analysis_error_message(error_msg)
                    socketio.emit("analysis_error", error_message, room=analysis_room)

            t = threading.Thread(target=analyze_task, daemon=True)
            t.start()

        except Exception as e:
            logger.exception("[WebSocket] 启动分析失败: %s", e)
            # 使用标准化消息格式
            error_message = create_analysis_error_message(str(e))
            emit("analysis_error", error_message)


def _emit_progress(socketio, room, image_id, current, total, success, failed, status, result=None, error=None, task_id=None):
    """
    发送分析进度消息（标准化格式）
    
    Args:
        socketio: SocketIO 实例
        room: 分析房间名（analysis_{client_id}），单一会话仅追加图片
        image_id: 图片ID
        current: 当前处理的图片序号
        total: 总图片数
        success: 成功数量
        failed: 失败数量
        status: 状态（'pending', 'analyzing', 'completed', 'error'）
        result: 分析结果（可选）
        error: 错误信息（可选）
        task_id: 任务ID（可选，用于获取 section 信息）
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
        section=section
    )
    
    # 记录发送的进度消息（用于调试）
    logger.info(
        f"[WebSocket] 发送分析进度: image_id={image_id}, status={status}, "
        f"current={current}/{total}, has_result={result is not None}, section_size={len(section) if section else 0}"
    )
    
    socketio.emit("analysis_progress", message, room=room)

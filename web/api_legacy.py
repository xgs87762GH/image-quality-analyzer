"""Web API接口 - 提供JSON数据（遗留端点，逐步迁移到 web/api/ 子模块）"""
import time
import json
from flask import Blueprint, jsonify, request
from typing import Dict, Any, Optional

try:
    from services.image_service import ImageService
    from services.quality_service import QualityService
    from database.connection import get_db
    from repositories.image_repository import ImageRepository
    from repositories.quality_repository import QualityRepository
    from repositories.metadata_repository import MetadataRepository
    from database.models import QualityAssessment
    from datetime import datetime
except ImportError:
    # 如果导入失败，说明核心模块未初始化
    ImageService = None
    QualityService = None

# 注意：此文件中的端点将逐步迁移到 web/api/ 子模块
# 目前保留用于向后兼容
api_bp = Blueprint('api_legacy', __name__, url_prefix='/api')


@api_bp.route('/stats', methods=['GET'])
def get_statistics():
    """获取统计信息"""
    try:
        if not QualityService or not ImageService:
            return jsonify({'success': False, 'error': '核心模块未初始化'}), 500
        quality_service = QualityService()
        image_service = ImageService()
        
        quality_stats = quality_service.get_statistics()
        image_stats = image_service.get_statistics()
        
        return jsonify({
            'success': True,
            'data': {
                'total_images': image_stats.get('total_images', 0),
                'quality_statistics': quality_stats
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/images', methods=['GET'])
def get_images():
    """获取图像列表"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        rating = request.args.get('rating', type=int)
        label = request.args.get('label')
        quality_min = request.args.get('quality_min', type=float)
        quality_max = request.args.get('quality_max', type=float)
        
        image_service = ImageService()
        quality_service = QualityService()
        
        # 根据条件查询
        if rating:
            results = quality_service.find_by_rating(rating, rating)
        elif label:
            results = quality_service.find_by_label(label)
        elif quality_min is not None or quality_max is not None:
            min_score = quality_min or 0.0
            max_score = quality_max or 100.0
            results = quality_service.find_by_quality_range(min_score, max_score)
        else:
            # 获取所有图像（不包括已删除的）
            db = get_db()
            image_repo = ImageRepository(db)
            images = image_repo.list_all(limit=per_page * 2, offset=(page - 1) * per_page, include_deleted=False)  # 多取一些，用于过滤
            from repositories.metadata_repository import MetadataRepository
            from pathlib import Path
            metadata_repo = MetadataRepository(db)
            results = []
            for img in images:
                # 检查源文件是否存在
                file_path = Path(img.file_path)
                if not file_path.exists():
                    # 源文件不存在，跳过
                    continue
                
                quality = quality_service.quality_repo.find_by_image_id(img.id)
                metadata = metadata_repo.find_by_image_id(img.id)
                result_item = {
                    'image': img.to_dict(),
                    'quality': quality.to_dict() if quality else {}
                }
                if metadata:
                    result_item['metadata'] = metadata.to_dict()
                results.append(result_item)
                
                # 如果已经获取足够的有效图片，停止
                if len(results) >= per_page:
                    break
        
        # 分页
        total = len(results)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_results = results[start:end]
        
        return jsonify({
            'success': True,
            'data': {
                'images': paginated_results,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/images/<int:image_id>', methods=['GET'])
def get_image_detail(image_id: int):
    """获取图像详细信息"""
    try:
        image_service = ImageService()
        image_info = image_service.get_image_info(image_id)
        
        if not image_info:
            return jsonify({
                'success': False,
                'error': 'Image not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': image_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/images/search', methods=['GET'])
def search_images():
    """搜索图像"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter is required'
            }), 400
        
        db = get_db()
        image_repo = ImageRepository(db)
        
        # 搜索文件名或路径
        cursor = db.execute(
            """
            SELECT * FROM images 
            WHERE file_name LIKE ? OR file_path LIKE ?
            LIMIT 50
            """,
            (f'%{query}%', f'%{query}%')
        )
        
        results = []
        quality_service = QualityService()
        for row in cursor.fetchall():
            image = image_repo.find_by_id(row['id'])
            if image:
                quality = quality_service.quality_repo.find_by_image_id(image.id)
                results.append({
                    'image': image.to_dict(),
                    'quality': quality.to_dict() if quality else None
                })
        
        return jsonify({
            'success': True,
            'data': {
                'images': results,
                'count': len(results)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/duplicates', methods=['GET'])
def get_duplicates():
    """获取重复图像"""
    try:
        image_service = ImageService()
        duplicates = image_service.find_duplicates()
        
        return jsonify({
            'success': True,
            'data': {
                'duplicates': duplicates,
                'count': len(duplicates)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/labels', methods=['GET'])
def get_labels():
    """获取所有标签统计"""
    try:
        db = get_db()
        cursor = db.execute(
            """
            SELECT label, COUNT(*) as count, AVG(quality_score) as avg_score
            FROM quality_assessments
            GROUP BY label
            ORDER BY count DESC
            """
        )
        
        labels = []
        for row in cursor.fetchall():
            labels.append({
                'label': row['label'],
                'count': row['count'],
                'avg_score': round(row['avg_score'], 2) if row['avg_score'] else None
            })
        
        return jsonify({
            'success': True,
            'data': labels
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/images/<int:image_id>/delete', methods=['POST'])
def delete_image(image_id: int):
    """删除图像（软删除，移动到回收站）"""
    try:
        if not ImageRepository:
            return jsonify({'success': False, 'error': '核心模块未初始化'}), 500
        
        db = get_db()
        image_repo = ImageRepository(db)
        
        success = image_repo.soft_delete(image_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '图像已移动到回收站'
            })
        else:
            return jsonify({
                'success': False,
                'error': '图像不存在或已被删除'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/images/batch-delete', methods=['POST'])
def batch_delete_images():
    """批量删除图像"""
    try:
        if not ImageRepository:
            return jsonify({'success': False, 'error': '核心模块未初始化'}), 500
        
        data = request.get_json()
        image_ids = data.get('image_ids', [])
        
        if not image_ids:
            return jsonify({
                'success': False,
                'error': '请提供要删除的图像ID列表'
            }), 400
        
        db = get_db()
        image_repo = ImageRepository(db)
        
        deleted_count = 0
        for image_id in image_ids:
            if image_repo.soft_delete(image_id):
                deleted_count += 1
        
        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_count}/{len(image_ids)} 个图像',
            'deleted_count': deleted_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/images/<int:image_id>/restore', methods=['POST'])
def restore_image(image_id: int):
    """从回收站恢复图像"""
    try:
        if not ImageRepository:
            return jsonify({'success': False, 'error': '核心模块未初始化'}), 500
        
        db = get_db()
        image_repo = ImageRepository(db)
        
        success = image_repo.restore(image_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '图像已恢复'
            })
        else:
            return jsonify({
                'success': False,
                'error': '图像不存在或未被删除'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/images/<int:image_id>/permanent-delete', methods=['POST'])
def permanent_delete_image(image_id: int):
    """永久删除图像（硬删除）"""
    try:
        if not ImageRepository:
            return jsonify({'success': False, 'error': '核心模块未初始化'}), 500
        
        db = get_db()
        image_repo = ImageRepository(db)
        
        success = image_repo.hard_delete(image_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '图像已永久删除'
            })
        else:
            return jsonify({
                'success': False,
                'error': '图像不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/trash', methods=['GET'])
def get_trash():
    """获取回收站图像列表"""
    try:
        if not ImageRepository:
            return jsonify({'success': False, 'error': '核心模块未初始化'}), 500
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        db = get_db()
        image_repo = ImageRepository(db)
        
        images = image_repo.list_deleted(limit=per_page, offset=(page - 1) * per_page)
        total = image_repo.count_deleted()
        
        # 获取质量信息
        quality_service = QualityService()
        results = []
        for img in images:
            quality = quality_service.quality_repo.find_by_image_id(img.id)
            results.append({
                'image': img.to_dict(),
                'quality': quality.to_dict() if quality else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'images': results,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/system-info', methods=['GET'])
def get_system_info():
    """获取系统信息"""
    try:
        from utils.system_info import get_system_info
        info = get_system_info()
        return jsonify({
            'success': True,
            'data': info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/settings/trash-dir', methods=['GET'])
def get_trash_dir():
    """获取回收站路径"""
    try:
        from config.settings import get_settings
        settings = get_settings()
        return jsonify({
            'success': True,
            'data': {
                'trash_dir': settings.trash.trash_dir
            }
        })
    except Exception as e:
        from utils.logger import get_logger
        logger = get_logger()
        logger.error(f"获取回收站路径失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/settings/trash-dir', methods=['POST'])
def set_trash_dir():
    """设置回收站路径"""
    try:
        from pathlib import Path
        from config.settings import get_settings, set_settings
        from utils.logger import get_logger
        
        logger = get_logger()
        data = request.get_json() or {}
        trash_dir = data.get('trash_dir', '').strip()
        
        settings = get_settings()
        
        # 如果为空，使用默认路径
        if not trash_dir:
            from config.settings import _get_default_trash_dir
            trash_dir = _get_default_trash_dir()
            logger.info(f"[设置] 使用默认回收站路径: {trash_dir}")
        else:
            # 验证路径
            trash_path = Path(trash_dir)
            try:
                # 确保目录存在
                trash_path.mkdir(parents=True, exist_ok=True)
                trash_dir = str(trash_path.absolute())
                logger.info(f"[设置] 设置回收站路径: {trash_dir}")
            except Exception as e:
                logger.error(f"[设置] 创建回收站目录失败: {trash_dir}, 错误: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': f'无法创建回收站目录: {e}'
                }), 400
        
        # 更新设置
        settings.trash.trash_dir = trash_dir
        
        # 保存到环境变量（通过设置全局配置）
        set_settings(settings)
        
        return jsonify({
            'success': True,
            'data': {
                'trash_dir': trash_dir
            }
        })
    except Exception as e:
        from utils.logger import get_logger
        logger = get_logger()
        logger.error(f"设置回收站路径失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/models/status', methods=['GET'])
def get_models_status():
    """获取模型状态"""
    try:
        from services.model_service import ModelService
        service = ModelService()
        status = service.check_model_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/models/download', methods=['POST'])
def download_model():
    """下载模型"""
    try:
        from services.model_service import ModelService
        data = request.get_json() or {}
        model_name = data.get('model_name', 'openai/clip-vit-base-patch32')
        
        service = ModelService()
        result = service.download_aesthetic_model(model_name)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/images/analyze', methods=['POST'])
def analyze_images():
    """手动分析图像（支持批量）"""
    # 立即初始化日志，确保可以记录
    from utils.logger import get_logger
    import datetime
    logger = get_logger()
    
    # 记录分析开始时间
    start_time = datetime.datetime.now()
    start_timestamp = start_time.strftime('%Y-%m-%d %H:%M:%S')
    
    logger.info("=" * 80)
    logger.info(f"[分析] ========== 分析任务开始 ========== 时间: {start_timestamp}")
    logger.info("=" * 80)
    
    try:
        data = request.get_json() or {}
        image_ids = data.get('image_ids', [])
        use_ai = data.get('use_ai', False)
        ai_model = data.get('ai_model', 'gpt4v')
        ai_api_key = data.get('ai_api_key')
        ollama_base_url = data.get('ollama_base_url', 'http://localhost:11434')
        ollama_model = data.get('ollama_model', 'llama2')
        aesthetic_mode = data.get('aesthetic_mode', 'none')  # 新增：审美评估方式
        write_xmp = data.get('write_xmp', True)  # 默认启用XMP写入
        
        # 获取评估问题数组
        evaluation_questions = data.get('evaluation_questions', [])
        
        logger.info(f"[分析] ========== 请求参数 ==========")
        logger.info(f"  - 图像数量: {len(image_ids)}")
        logger.info(f"  - 图像ID列表: {image_ids}")
        logger.info(f"  - AI分析: {'✓ 启用' if use_ai else '✗ 禁用'}")
        logger.info(f"  - 审美评估方式: {aesthetic_mode}")
        logger.info(f"  - XMP写入: {'✓ 启用' if write_xmp else '✗ 禁用'}")
        logger.info(f"  - 评估问题数量: {len(evaluation_questions)}")
        if evaluation_questions:
            logger.info(f"  - 评估问题详情:")
            for idx, q in enumerate(evaluation_questions, 1):
                issue = q.get('issue', '')
                return_type = q.get('return_type', 'array')
                return_spec = q.get('return_spec', '')
                logger.info(f"    [{idx}] issue: {issue}, return_type: {return_type}, return_spec: {return_spec}")
        if use_ai:
            logger.info(f"  - AI模型: {ai_model}")
            if ai_model == 'ollama':
                logger.info(f"  - Ollama地址: {ollama_base_url}")
                logger.info(f"  - Ollama模型: {ollama_model}")
        logger.info(f"[分析] ================================")
        
        if not image_ids:
            logger.warning("[分析] 错误: 未指定图像ID")
            return jsonify({
                'success': False,
                'error': '未指定图像ID'
            }), 400
        
        from services.image_service import ImageService
        from services.quality_service import QualityService
        from analyzers.ai_analyzer import AIAnalyzer
        
        image_service = ImageService()
        quality_service = QualityService()
        results = []
        
        total = len(image_ids)
        logger.info(f"[分析] 开始处理 {total} 张图像（串行处理模式）")
        logger.info("-" * 80)
        
        # 逐张分析图像（串行处理，避免一次性处理太多）
        for idx, image_id in enumerate(image_ids, 1):
            image_start_time = time.time()
            progress_percent = (idx / total) * 100
            
            # 初始化metadata变量（在try块之前，确保在所有路径中都可访问）
            metadata = None
            from repositories.metadata_repository import MetadataRepository
            metadata_repo = MetadataRepository(get_db())
            
            try:
                logger.info(f"[进度] [{idx}/{total}] ({progress_percent:.1f}%) 开始分析图像 ID={image_id}")
                
                # 获取图像信息
                image = image_service.image_repo.find_by_id(image_id)
                if not image:
                    logger.warning(f"[进度] [{idx}/{total}] 图像不存在: ID={image_id}")
                    results.append({
                        'image_id': image_id,
                        'success': False,
                        'error': '图像不存在',
                        'progress': {
                            'current': idx,
                            'total': total,
                            'percent': progress_percent
                        }
                    })
                    continue
                
                logger.info(f"[进度] [{idx}/{total}] 图像路径: {image.file_path}")
                
                # 执行质量分析
                quality_start = time.time()
                logger.info(f"[进度] [{idx}/{total}] 开始质量分析...")
                from analyzers.image_analyzer import ImageAnalyzer
                
                # 根据审美评估方式创建分析器
                ai_analyzer_for_aesthetic = None
                if aesthetic_mode == 'ai':
                    # 创建AI分析器用于审美评估
                    ai_analyzer_for_aesthetic = AIAnalyzer(
                        model=ai_model,
                        api_key=ai_api_key,
                        ollama_base_url=ollama_base_url,
                        ollama_model=ollama_model
                    )
                    logger.info(f"[进度] [{idx}/{total}] 使用AI模型评估审美: {ai_model}")
                elif aesthetic_mode == 'clip':
                    logger.info(f"[进度] [{idx}/{total}] 使用CLIP模型评估审美")
                
                analyzer = ImageAnalyzer(
                    aesthetic_mode=aesthetic_mode,
                    ai_analyzer=ai_analyzer_for_aesthetic
                )
                analysis = analyzer.analyze(image.file_path)
                quality_duration = time.time() - quality_start
                
                # 检查分析结果
                if not analysis:
                    logger.warning(f"[进度] [{idx}/{total}] 质量分析失败: 无法读取或处理图像")
                    results.append({
                        'image_id': image_id,
                        'success': False,
                        'error': '图像分析失败：无法读取或处理图像',
                        'progress': {
                            'current': idx,
                            'total': total,
                            'percent': progress_percent
                        }
                    })
                    continue
                
                logger.info(f"[进度] [{idx}/{total}] 质量分析完成 (耗时: {quality_duration:.2f}秒, 质量分数: {analysis.get('quality_score', 0):.2f})")
                
                # 保存质量评估（使用 create_or_update 方法）
                metrics = analysis.get('metrics', {})
                analysis_result = {
                    'quality_score': analysis.get('quality_score', 0),
                    'rating': analysis.get('rating', 0),
                    'label': analysis.get('label', ''),
                    'metrics': {
                        'blur_score': metrics.get('blur_score'),
                        'brightness': metrics.get('brightness'),
                        'entropy': metrics.get('entropy'),
                        'brisque': metrics.get('brisque'),
                        'aesthetic_score': metrics.get('aesthetic_score')
                    }
                }
                quality = quality_service.quality_repo.create_or_update(image_id, analysis_result)
                logger.debug(f"[进度] [{idx}/{total}] 质量评估已保存: ID={quality.id if hasattr(quality, 'id') else 'N/A'}")
                
                # 保存XMP元数据到数据库（即使不写入文件，也保存到数据库以便查询）
                xmp_data_for_db = {
                    'rating': analysis.get('rating', 0),
                    'label': analysis.get('label', ''),
                    'subjects': analysis.get('subjects', []),
                    'description': f"QualityAnalysis: {json.dumps(analysis_result.get('metrics', {}), ensure_ascii=False)}"
                }
                metadata = metadata_repo.create_or_update(image_id, xmp_data_for_db)
                logger.debug(f"[进度] [{idx}/{total}] XMP元数据已保存到数据库: ID={metadata.id if hasattr(metadata, 'id') else 'N/A'}")
                
                # AI分析（如果启用）
                ai_analysis = None
                ai_duration = None
                
                # 确保metadata已初始化（在所有代码路径之前，避免Python作用域问题）
                metadata = metadata_repo.find_by_image_id(image_id) if metadata is None else metadata
                
                if use_ai:
                    try:
                        logger.info(f"[进度] [{idx}/{total}] ========== 开始AI分析 ==========")
                        logger.info(f"[进度] [{idx}/{total}] AI模型: {ai_model}")
                        if ai_model == 'ollama':
                            logger.info(f"[进度] [{idx}/{total}] Ollama配置: {ollama_base_url} / {ollama_model}")
                        
                        if evaluation_questions:
                            logger.info(f"[进度] [{idx}/{total}] ✓ 检测到评估问题，数量: {len(evaluation_questions)}")
                            for q_idx, q in enumerate(evaluation_questions, 1):
                                issue = q.get('issue', '')
                                return_type = q.get('return_type', 'array')
                                return_spec = q.get('return_spec', '')
                                logger.info(f"[进度] [{idx}/{total}]   问题[{q_idx}]: issue='{issue}', return_type='{return_type}', return_spec={return_spec}")
                        else:
                            logger.info(f"[进度] [{idx}/{total}] ✗ 未配置评估问题")
                        
                        ai_analyzer = AIAnalyzer(
                            model=ai_model,
                            api_key=ai_api_key,
                            ollama_base_url=ollama_base_url,
                            ollama_model=ollama_model
                        )
                        ai_start_time = time.time()
                        ai_result = ai_analyzer.analyze_image(
                            image.file_path,
                            evaluation_questions=evaluation_questions if evaluation_questions else None
                        )
                        ai_duration = time.time() - ai_start_time
                        
                        if ai_result.get('success'):
                            ai_analysis = ai_result.get('analysis')
                            # 新格式：评估结果数组
                            evaluations_from_ai = ai_result.get('evaluations', [])
                            analysis_len = len(ai_analysis) if ai_analysis else 0
                            logger.info(f"[进度] [{idx}/{total}] ✓ AI分析成功 (耗时: {ai_duration:.2f}秒, 响应长度: {analysis_len}字符)")
                            
                            # 详细记录评估结果
                            if evaluations_from_ai:
                                logger.info(f"[进度] [{idx}/{total}] ✓ 评估结果解析成功，数量: {len(evaluations_from_ai)}")
                                for eval_idx, eval_item in enumerate(evaluations_from_ai, 1):
                                    issue = eval_item.get('issue', '')
                                    result = eval_item.get('result', '')
                                    logger.info(f"[进度] [{idx}/{total}]   结果[{eval_idx}]: issue='{issue}', result='{result}'")
                            else:
                                logger.warning(f"[进度] [{idx}/{total}] ✗ AI分析未返回评估结果")
                                logger.warning(f"[进度] [{idx}/{total}]   - evaluations_from_ai值: {evaluations_from_ai}")
                                logger.warning(f"[进度] [{idx}/{total}]   - ai_result完整内容: {ai_result}")
                                if evaluation_questions:
                                    logger.warning(f"[进度] [{idx}/{total}]   - 已配置评估问题但未返回结果，可能原因:")
                                    logger.warning(f"[进度] [{idx}/{total}]     1. AI响应格式不符合要求")
                                    logger.warning(f"[进度] [{idx}/{total}]     2. JSON解析失败")
                                    logger.warning(f"[进度] [{idx}/{total}]     3. 评估问题定义格式错误")
                            
                            # 保存AI分析结果和评估结果到数据库（使用评估服务）
                            from services.evaluation_service import EvaluationService
                            
                            eval_service = EvaluationService()
                            
                            # metadata已在前面初始化，这里只需要确保存在
                            metadata = metadata_repo.find_by_image_id(image_id) if not metadata else metadata
                            
                            # 处理评估问题（支持数组格式，高内聚：评估结果处理逻辑集中）
                            if evaluations_from_ai:
                                # 获取现有评估问题列表
                                existing_evaluations = []
                                if metadata and metadata.evaluations:
                                    existing_evaluations = eval_service.deserialize_evaluations(metadata.evaluations)
                                
                                # 更新评估结果（使用AI返回的结构化结果）
                                updated_evaluations = existing_evaluations.copy() if existing_evaluations else []
                                
                                # 合并AI返回的评估结果（使用issue字段）
                                for eval_item in evaluations_from_ai:
                                    issue = eval_item.get('issue', '')
                                    result = eval_item.get('result', '')
                                    if issue:
                                        # 查找是否已存在该问题
                                        found = False
                                        for existing in updated_evaluations:
                                            if existing.get('issue') == issue:
                                                existing['result'] = result
                                                found = True
                                                break
                                        if not found:
                                            updated_evaluations.append({
                                                'issue': issue,
                                                'result': result
                                            })
                                
                                logger.info(f"[进度] [{idx}/{total}] ✓ 评估结果合并完成，最终数量: {len(updated_evaluations)}")
                                for eval_idx, eval_item in enumerate(updated_evaluations, 1):
                                    issue = eval_item.get('issue', '')
                                    result = eval_item.get('result', '')
                                    logger.info(f"[进度] [{idx}/{total}]   最终[{eval_idx}]: issue='{issue}', result='{result}'")
                                
                                # 序列化为JSON
                                evaluations_json = eval_service.serialize_evaluations(updated_evaluations)
                                logger.info(f"[进度] [{idx}/{total}] ✓ 序列化完成，JSON长度: {len(evaluations_json) if evaluations_json else 0}字符")
                                if evaluations_json:
                                    logger.debug(f"[进度] [{idx}/{total}] JSON内容: {evaluations_json[:200]}...")
                            else:
                                evaluations_json = None
                            
                            if metadata:
                                metadata.ai_analysis = ai_analysis
                                if evaluations_json is not None:
                                    metadata.evaluations = evaluations_json
                                    logger.info(f"[进度] [{idx}/{total}] ✓ 保存评估结果到数据库 (metadata.id={metadata.id})")
                                else:
                                    logger.warning(f"[进度] [{idx}/{total}] ✗ evaluations_json为None，未保存评估结果")
                                metadata_repo.update(metadata)
                                logger.info(f"[进度] [{idx}/{total}] ✓ metadata更新完成")
                            else:
                                # 创建新的metadata记录
                                from database.models import Metadata
                                metadata = Metadata(
                                    image_id=image_id,
                                    ai_analysis=ai_analysis,
                                    evaluations=evaluations_json
                                )
                                with get_db().transaction() as conn:
                                    cursor = conn.execute(
                                        f"""
                                        INSERT INTO {Metadata.TABLE_NAME}
                                        (image_id, ai_analysis, evaluations)
                                        VALUES (?, ?, ?)
                                        """,
                                        (
                                            metadata.image_id,
                                            metadata.ai_analysis,
                                            metadata.evaluations
                                        )
                                    )
                                    metadata.id = cursor.lastrowid
                        else:
                            error_msg = ai_result.get('error', '未知错误')
                            logger.warning(f"[进度] [{idx}/{total}] AI分析失败 (耗时: {ai_duration:.2f}秒): {error_msg}")
                            # 注意：不能在这里检查metadata is None，因为Python会认为metadata是局部变量
                            # 由于metadata已经在第643行初始化，这里直接重新获取以确保它存在
                            # 如果metadata已经存在且不为None，这个赋值不会造成问题
                            metadata = metadata_repo.find_by_image_id(image_id)
                    except Exception as ai_error:
                        ai_duration = time.time() - ai_start_time if 'ai_start_time' in locals() else 0
                        logger.error(f"[进度] [{idx}/{total}] AI分析异常 (耗时: {ai_duration:.2f}秒): {str(ai_error)}", exc_info=True)
                        # AI分析失败不影响整体分析结果
                        # 确保metadata已初始化（即使发生异常）
                        # 注意：不能在这里检查metadata is None，直接重新获取
                        metadata = metadata_repo.find_by_image_id(image_id)
                
                image_duration = time.time() - image_start_time
                # 获取评估问题数组（如果有）
                evaluations_list = []
                # 确保metadata已初始化（在使用之前）
                # 注意：不能在这里检查metadata is None，直接重新获取
                metadata = metadata_repo.find_by_image_id(image_id)
                if metadata and metadata.evaluations:
                    from services.evaluation_service import EvaluationService
                    eval_service = EvaluationService()
                    evaluations_list = eval_service.deserialize_evaluations(metadata.evaluations)
                else:
                    evaluations_list = []
                
                # 写入XMP元数据（如果启用）
                xmp_written = False
                if write_xmp:
                    try:
                        from metadata.xmp_writer import XMPWriter
                        from metadata.keyword_extractor import extract_keywords_from_ai_analysis, extract_keywords_from_evaluations
                        from config.settings import get_settings
                        
                        # 自动检测项目内或系统PATH中的ExifTool
                        xmp_writer = XMPWriter()
                        if xmp_writer.is_available():
                            # 准备XMP数据
                            xmp_data = {
                                'rating': analysis.get('rating', 0),
                                'label': analysis.get('label', ''),
                                'subjects': analysis.get('subjects', []),
                                'metrics': analysis.get('metrics', {})
                            }
                            
                            # 从AI分析中提取关键词
                            ai_keywords = []
                            if ai_analysis:
                                ai_keywords = extract_keywords_from_ai_analysis(ai_analysis, max_keywords=10)
                                if ai_keywords:
                                    logger.debug(f"[进度] [{idx}/{total}] 从AI分析中提取了 {len(ai_keywords)} 个关键词")
                            
                            # 从评估结果中提取关键词
                            if evaluations_list:
                                eval_keywords = extract_keywords_from_evaluations(evaluations_list)
                                if eval_keywords:
                                    ai_keywords.extend(eval_keywords)
                                    logger.debug(f"[进度] [{idx}/{total}] 从评估结果中提取了 {len(eval_keywords)} 个关键词")
                            
                            # 合并AI关键词
                            if ai_keywords:
                                xmp_data['ai_keywords'] = ai_keywords
                            
                            # 添加描述（如果有AI分析）
                            if ai_analysis:
                                # 截取AI分析的前200字符作为描述
                                ai_desc = ai_analysis[:200] + "..." if len(ai_analysis) > 200 else ai_analysis
                                xmp_data['description'] = ai_desc
                            
                            success = xmp_writer.write(
                                image.file_path,
                                xmp_data,
                                backup=get_settings().metadata.backup_original
                            )
                            if success:
                                xmp_written = True
                                keyword_count = len(ai_keywords) if ai_keywords else 0
                                logger.info(f"[进度] [{idx}/{total}] ✓ XMP元数据已写入: {image.file_path} (关键词: {keyword_count}个)")
                            else:
                                logger.warning(f"[进度] [{idx}/{total}] ✗ XMP元数据写入失败: {image.file_path}")
                        else:
                            logger.warning(f"[进度] [{idx}/{total}] ✗ ExifTool不可用，跳过XMP写入")
                    except Exception as xmp_error:
                        logger.warning(f"[进度] [{idx}/{total}] ✗ XMP写入异常: {str(xmp_error)}")
                
                results.append({
                    'image_id': image_id,
                    'success': True,
                    'quality_score': analysis.get('quality_score', 0),
                    'rating': analysis.get('rating', 0),
                    'label': analysis.get('label', ''),
                    'ai_analysis': ai_analysis,
                    'ai_duration': ai_duration,
                    'quality_duration': quality_duration,
                    'total_duration': image_duration,
                    'evaluations': evaluations_list,
                    'progress': {
                        'current': idx,
                        'total': total,
                        'percent': progress_percent
                    }
                })
                
                logger.info(f"[进度] [{idx}/{total}] ✓ 图像分析完成 (总耗时: {image_duration:.2f}秒, 质量分数: {analysis.get('quality_score', 0):.2f})")
                logger.info("-" * 80)
                
            except Exception as e:
                image_duration = time.time() - image_start_time
                # 记录详细错误日志
                logger.error(f"[进度] [{idx}/{total}] ✗ 分析失败 (耗时: {image_duration:.2f}秒): {str(e)}", exc_info=True)
                import traceback
                logger.error(f"[进度] [{idx}/{total}] 错误堆栈: {traceback.format_exc()}")
                
                results.append({
                    'image_id': image_id,
                    'success': False,
                    'error': str(e),
                    'progress': {
                        'current': idx,
                        'total': total,
                        'percent': progress_percent
                    }
                })
                logger.info("-" * 80)
        
        # 计算总耗时
        end_time = datetime.datetime.now()
        end_timestamp = end_time.strftime('%Y-%m-%d %H:%M:%S')
        total_duration = (end_time - start_time).total_seconds()
        
        success_count = sum(1 for r in results if r.get('success', False))
        fail_count = len(results) - success_count
        
        logger.info("=" * 80)
        logger.info(f"[分析] ========== 分析任务完成 ==========")
        logger.info(f"[分析] 开始时间: {start_timestamp}")
        logger.info(f"[分析] 结束时间: {end_timestamp}")
        logger.info(f"[分析] 总耗时: {total_duration:.2f}秒 ({total_duration/60:.2f}分钟)")
        logger.info(f"[分析] 处理结果: 总计 {total} 张, 成功 {success_count} 张, 失败 {fail_count} 张")
        if total > 0:
            avg_time = total_duration / total
            logger.info(f"[分析] 平均每张耗时: {avg_time:.2f}秒")
        logger.info("=" * 80)
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total': total,
                'success': success_count,
                'failed': fail_count
            }
        })
    except Exception as e:
        # 记录顶层错误日志
        from utils.logger import get_logger
        import traceback
        logger = get_logger()
        logger.error(f"[分析] 批量分析失败: {str(e)}", exc_info=True)
        logger.error(f"[分析] 错误堆栈: {traceback.format_exc()}")
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/images/<int:image_id>/ai-analyze', methods=['POST'])
def ai_analyze_image(image_id: int):
    """AI分析单个图像"""
    try:
        data = request.get_json() or {}
        ai_model = data.get('model', 'gpt4v')
        ai_api_key = data.get('api_key')
        ollama_base_url = data.get('ollama_base_url', 'http://localhost:11434')
        ollama_model = data.get('ollama_model', 'llama2')
        prompt = data.get('prompt')
        
        # Ollama不需要API密钥
        if ai_model != 'ollama' and not ai_api_key:
            return jsonify({
                'success': False,
                'error': 'API密钥未提供'
            }), 400
        
        from services.image_service import ImageService
        from analyzers.ai_analyzer import AIAnalyzer
        
        image_service = ImageService()
        image = image_service.image_repo.find_by_id(image_id)
        
        if not image:
            return jsonify({
                'success': False,
                'error': '图像不存在'
            }), 404
        
        ai_analyzer = AIAnalyzer(
            model=ai_model,
            api_key=ai_api_key,
            ollama_base_url=ollama_base_url,
            ollama_model=ollama_model
        )
        result = ai_analyzer.analyze_image(image.file_path, prompt)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/ollama/models', methods=['GET'])
def get_ollama_models():
    """获取Ollama可用模型列表"""
    try:
        from analyzers.ai_analyzer import AIAnalyzer
        
        base_url = request.args.get('base_url', 'http://localhost:11434')
        analyzer = AIAnalyzer(model='ollama', ollama_base_url=base_url)
        result = analyzer.get_ollama_models()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/images/import', methods=['POST'])
def import_images():
    """批量导入图像（从多个目录）- 使用服务层（低耦合）"""
    try:
        from services.auto_import_service import AutoImportService
        
        data = request.get_json() or {}
        directories = data.get('directories', [])
        
        if not directories:
            return jsonify({
                'success': False,
                'error': '未指定目录'
            }), 400
        
        # 使用服务层处理（低耦合）
        service = AutoImportService()
        result = service.import_from_directories(directories, silent=False)
        
        # 统一返回格式
        return jsonify({
            'success': result['success'],
            'message': result.get('message', ''),
            'error': result.get('error', ''),
            'total': result.get('total', 0),
            'success': result.get('success_count', 0),
            'failed': result.get('failed_count', 0),
            'invalid_directories': result.get('invalid_directories', [])
        })
    except Exception as e:
        from utils.logger import get_logger
        logger = get_logger()
        logger.error(f"[导入] 批量导入失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/images/auto-import', methods=['POST'])
def auto_import_images():
    """自动导入图像（从设置的目录）- 静默模式"""
    try:
        from services.auto_import_service import AutoImportService
        
        data = request.get_json() or {}
        directories = data.get('directories', [])
        clear_database = data.get('clear_database', False)
        
        # 使用服务层处理，静默模式（不输出详细信息）
        service = AutoImportService()
        result = service.import_from_directories(
            directories, 
            silent=True,
            clear_database=clear_database
        )
        
        return jsonify({
            'success': result['success'],
            'message': result.get('message', ''),
            'total': result.get('total', 0),
            'success_count': result.get('success_count', 0),
            'failed_count': result.get('failed_count', 0),
            'new_count': result.get('new_count', 0),
            'existing_count': result.get('existing_count', 0),
            'deleted_count': result.get('deleted_count', 0)
        })
    except Exception as e:
        from utils.logger import get_logger
        logger = get_logger()
        logger.error(f"[自动导入] 自动导入失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/images/cleanup', methods=['POST'])
def cleanup_images():
    """清理脏数据：删除源文件不存在的图片记录"""
    try:
        from utils.logger import get_logger
        from pathlib import Path
        logger = get_logger()
        
        db = get_db()
        image_repo = ImageRepository(db)
        
        # 获取所有未删除的图片
        all_images = image_repo.list_all(include_deleted=False)
        
        deleted_count = 0
        for img in all_images:
            file_path = Path(img.file_path)
            if not file_path.exists():
                # 源文件不存在，删除记录
                logger.info(f"[清理] 删除不存在的图片记录: {img.file_path} (ID: {img.id})")
                image_repo.hard_delete(img.id)
                deleted_count += 1
        
        logger.info(f"[清理] 清理完成，删除了 {deleted_count} 条脏数据")
        
        return jsonify({
            'success': True,
            'message': f'清理完成，删除了 {deleted_count} 条脏数据',
            'deleted_count': deleted_count
        })
    except Exception as e:
        from utils.logger import get_logger
        logger = get_logger()
        logger.error(f"[清理] 清理失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/directories/validate', methods=['POST'])
def validate_directories():
    """验证目录列表，返回存在的目录"""
    try:
        from pathlib import Path
        from utils.logger import get_logger
        logger = get_logger()
        
        data = request.get_json() or {}
        directories = data.get('directories', [])
        
        if not directories:
            return jsonify({
                'success': True,
                'valid_directories': [],
                'removed_count': 0
            })
        
        valid_directories = []
        removed_directories = []
        
        for directory in directories:
            dir_path = Path(directory)
            if dir_path.exists() and dir_path.is_dir():
                valid_directories.append(directory)
            else:
                removed_directories.append(directory)
                logger.info(f"[目录验证] 移除不存在的目录: {directory}")
        
        removed_count = len(removed_directories)
        if removed_count > 0:
            logger.info(f"[目录验证] 验证完成: 有效 {len(valid_directories)} 个, 移除 {removed_count} 个")
        
        return jsonify({
            'success': True,
            'valid_directories': valid_directories,
            'removed_directories': removed_directories,
            'removed_count': removed_count
        })
    except Exception as e:
        from utils.logger import get_logger
        logger = get_logger()
        logger.error(f"[目录验证] 验证失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/evaluations/clear', methods=['POST'])
def clear_evaluations():
    """批量清理评估数据（质量评估、自定义评估）"""
    try:
        from utils.logger import get_logger
        logger = get_logger()
        
        data = request.get_json() or {}
        image_ids = data.get('image_ids', [])
        clear_quality = data.get('clear_quality', False)  # 是否清理质量评估
        clear_custom = data.get('clear_custom', False)  # 是否清理自定义评估
        
        if not image_ids:
            return jsonify({
                'success': False,
                'error': '请选择要清理的图像'
            }), 400
        
        if not clear_quality and not clear_custom:
            return jsonify({
                'success': False,
                'error': '请至少选择一种评估类型'
            }), 400
        
        db = get_db()
        quality_repo = QualityRepository(db)
        metadata_repo = MetadataRepository(db)
        
        cleared_count = 0
        quality_cleared = 0
        custom_cleared = 0
        
        logger.info(f"[清理评估] 开始清理 {len(image_ids)} 张图像的评估数据")
        logger.info(f"[清理评估] 清理质量评估: {clear_quality}, 清理自定义评估: {clear_custom}")
        
        for image_id in image_ids:
            try:
                # 清理质量评估
                if clear_quality:
                    quality = quality_repo.find_by_image_id(image_id)
                    if quality:
                        db.execute(
                            f"DELETE FROM {QualityAssessment.TABLE_NAME} WHERE image_id = ?",
                            (image_id,)
                        )
                        quality_cleared += 1
                        logger.debug(f"[清理评估] 已清理图像 {image_id} 的质量评估")
                
                # 清理自定义评估（evaluations字段）
                if clear_custom:
                    metadata = metadata_repo.find_by_image_id(image_id)
                    if metadata:
                        metadata.evaluations = None
                        metadata.updated_at = datetime.now()
                        metadata_repo.update(metadata)
                        custom_cleared += 1
                        logger.debug(f"[清理评估] 已清理图像 {image_id} 的自定义评估")
                
                cleared_count += 1
            except Exception as e:
                logger.error(f"[清理评估] 清理图像 {image_id} 失败: {e}", exc_info=True)
        
        db.get_connection().commit()
        
        logger.info(f"[清理评估] 清理完成: 共 {cleared_count} 张图像, 质量评估 {quality_cleared} 个, 自定义评估 {custom_cleared} 个")
        
        return jsonify({
            'success': True,
            'data': {
                'cleared_count': cleared_count,
                'quality_cleared': quality_cleared,
                'custom_cleared': custom_cleared
            }
        })
    except Exception as e:
        from utils.logger import get_logger
        logger = get_logger()
        logger.error(f"[清理评估] 清理失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/images/advanced-search', methods=['GET'])
def advanced_search_images():
    """高级搜索图像（支持元数据、评估描述、评估结果）"""
    try:
        from utils.logger import get_logger
        logger = get_logger()
        
        # 获取搜索参数
        metadata_query = request.args.get('metadata', '').strip()  # 元数据搜索（EXIF、XMP等）
        evaluation_issue = request.args.get('evaluation_issue', '').strip()  # 评估问题描述
        evaluation_result = request.args.get('evaluation_result', '').strip()  # 评估结果
        quality_min = request.args.get('quality_min', type=float)  # 质量分数最小值
        quality_max = request.args.get('quality_max', type=float)  # 质量分数最大值
        rating = request.args.get('rating', type=int)  # 评级
        label = request.args.get('label', '').strip()  # 标签
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        db = get_db()
        image_repo = ImageRepository(db)
        quality_repo = QualityRepository(db)
        metadata_repo = MetadataRepository(db)
        
        # 构建查询条件
        conditions = []
        params = []
        
        # 元数据搜索（EXIF、XMP描述等）
        if metadata_query:
            conditions.append("""
                (m.exif_data LIKE ? OR m.xmp_description LIKE ? OR m.ai_analysis LIKE ?)
            """)
            pattern = f'%{metadata_query}%'
            params.extend([pattern, pattern, pattern])
        
        # 评估问题描述搜索
        if evaluation_issue:
            conditions.append("m.evaluations LIKE ?")
            params.append(f'%"issue":"%{evaluation_issue}%')
        
        # 评估结果搜索
        if evaluation_result:
            conditions.append("m.evaluations LIKE ?")
            params.append(f'%"result":"%{evaluation_result}%')
        
        # 质量分数范围
        if quality_min is not None:
            conditions.append("q.quality_score >= ?")
            params.append(quality_min)
        if quality_max is not None:
            conditions.append("q.quality_score <= ?")
            params.append(quality_max)
        
        # 评级
        if rating:
            conditions.append("q.rating = ?")
            params.append(rating)
        
        # 标签
        if label:
            conditions.append("q.label = ?")
            params.append(label)
        
        # 构建SQL查询
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 计算总数
        count_sql = f"""
            SELECT COUNT(DISTINCT i.id) as total
            FROM images i
            LEFT JOIN quality_assessments q ON i.id = q.image_id
            LEFT JOIN metadata m ON i.id = m.image_id
            WHERE i.deleted_at IS NULL AND ({where_clause})
        """
        
        cursor = db.execute(count_sql, params)
        total = cursor.fetchone()['total']
        
        # 获取分页数据
        offset = (page - 1) * per_page
        search_sql = f"""
            SELECT DISTINCT i.*, q.quality_score, q.rating, q.label, 
                   m.evaluations, m.ai_analysis, m.exif_data
            FROM images i
            LEFT JOIN quality_assessments q ON i.id = q.image_id
            LEFT JOIN metadata m ON i.id = m.image_id
            WHERE i.deleted_at IS NULL AND ({where_clause})
            ORDER BY i.created_at DESC
            LIMIT ? OFFSET ?
        """
        
        params.extend([per_page, offset])
        cursor = db.execute(search_sql, params)
        
        results = []
        for row in cursor.fetchall():
            image = image_repo.find_by_id(row['id'])
            if image:
                quality = quality_repo.find_by_image_id(image.id)
                metadata = metadata_repo.find_by_image_id(image.id)
                
                results.append({
                    'image': image.to_dict(),
                    'quality': quality.to_dict() if quality else None,
                    'metadata': metadata.to_dict() if metadata else None
                })
        
        logger.info(f"[高级搜索] 搜索完成: 共 {total} 条结果, 当前页 {len(results)} 条")
        
        return jsonify({
            'success': True,
            'data': {
                'images': results,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        from utils.logger import get_logger
        logger = get_logger()
        logger.error(f"[高级搜索] 搜索失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# 缩略图路由已移至app.py，避免路由冲突

"""图像相关API端点 - CRUD操作、搜索、删除等"""
from flask import jsonify, request
from pathlib import Path
from typing import List, Dict, Any

from . import api_bp
from services.service_factory import ServiceFactory
from database.connection import get_db
from repositories.image_repository import ImageRepository
from repositories.metadata_repository import MetadataRepository


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
        
        image_service = ServiceFactory.get_image_service()
        quality_service = ServiceFactory.get_quality_service()
        
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
            images = image_repo.list_all(limit=per_page * 2, offset=(page - 1) * per_page, include_deleted=False)
            metadata_repo = MetadataRepository(db)
            results = []
            for img in images:
                # 检查源文件是否存在
                file_path = Path(img.file_path)
                if not file_path.exists():
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
        image_service = ServiceFactory.get_image_service()
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
        quality_service = ServiceFactory.get_quality_service()
        
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


@api_bp.route('/images/<int:image_id>/delete', methods=['POST'])
def delete_image(image_id: int):
    """删除图像（软删除，移动到回收站）"""
    try:
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
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        db = get_db()
        image_repo = ImageRepository(db)
        quality_service = ServiceFactory.get_quality_service()
        
        images = image_repo.list_deleted(limit=per_page, offset=(page - 1) * per_page)
        total = image_repo.count_deleted()
        
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


@api_bp.route('/evaluations/clear', methods=['POST'])
def clear_evaluations():
    """批量清理评估数据（质量评估、自定义评估）"""
    try:
        from utils.logger import get_logger
        from repositories.quality_repository import QualityRepository
        from database.models import QualityAssessment, Metadata
        from datetime import datetime
        
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
        
        # 使用事务确保数据一致性
        with db.transaction() as conn:
            for image_id in image_ids:
                try:
                    # 清理质量评估
                    if clear_quality:
                        quality = quality_repo.find_by_image_id(image_id)
                        if quality:
                            cursor = conn.execute(
                                f"DELETE FROM {QualityAssessment.TABLE_NAME} WHERE image_id = ?",
                                (image_id,)
                            )
                            if cursor.rowcount > 0:
                                quality_cleared += 1
                                logger.debug(f"[清理评估] 已清理图像 {image_id} 的质量评估")
                    
                    # 清理自定义评估（evaluations字段）
                    if clear_custom:
                        metadata = metadata_repo.find_by_image_id(image_id)
                        if metadata:
                            # 直接使用 SQL 更新，避免事务嵌套问题
                            cursor = conn.execute(
                                f"UPDATE {Metadata.TABLE_NAME} SET evaluations = NULL, updated_at = ? WHERE id = ?",
                                (datetime.now().isoformat(), metadata.id)
                            )
                            if cursor.rowcount > 0:
                                custom_cleared += 1
                                logger.debug(f"[清理评估] 已清理图像 {image_id} 的自定义评估")
                    
                    cleared_count += 1
                except Exception as e:
                    logger.error(f"[清理评估] 清理图像 {image_id} 失败: {e}", exc_info=True)
                    # 继续处理其他图像，不中断整个流程
        
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

"""图像相关API端点 - CRUD操作、搜索、删除等"""
from flask import jsonify, request
from pathlib import Path
from typing import List, Dict, Any
import json

from . import api_bp
from services.service_factory import ServiceFactory
from database.connection import get_db
from repositories.image_repository import ImageRepository
from repositories.metadata_repository import MetadataRepository


def extract_camera_info_from_exif(metadata_dict: Dict[str, Any]) -> Dict[str, Any]:
    """从 exif_data 中提取相机信息并添加到 metadata_dict"""
    if not metadata_dict.get('exif_data'):
        return metadata_dict
    
    try:
        exif_data = json.loads(metadata_dict['exif_data']) if isinstance(metadata_dict['exif_data'], str) else metadata_dict['exif_data']
        if not isinstance(exif_data, dict):
            return metadata_dict
        
        # 尝试多种可能的键名（不同格式的 EXIF 数据可能使用不同的键名）
        # 直接键名
        if not metadata_dict.get('camera_make'):
            metadata_dict['camera_make'] = exif_data.get('Make') or exif_data.get('make')
        if not metadata_dict.get('camera_model'):
            metadata_dict['camera_model'] = exif_data.get('Model') or exif_data.get('model')
        if not metadata_dict.get('exposure_time'):
            metadata_dict['exposure_time'] = exif_data.get('ExposureTime') or exif_data.get('exposure_time')
        if not metadata_dict.get('f_number'):
            metadata_dict['f_number'] = exif_data.get('FNumber') or exif_data.get('f_number') or exif_data.get('ApertureValue')
        if not metadata_dict.get('iso'):
            iso_val = exif_data.get('ISO') or exif_data.get('iso') or exif_data.get('ISOSpeedRatings')
            if iso_val:
                try:
                    metadata_dict['iso'] = int(iso_val) if isinstance(iso_val, (int, float, str)) else None
                except (ValueError, TypeError):
                    pass
        if not metadata_dict.get('focal_length'):
            metadata_dict['focal_length'] = exif_data.get('FocalLength') or exif_data.get('focal_length')
        
        # EXIF: 前缀的键名
        if not metadata_dict.get('camera_make'):
            metadata_dict['camera_make'] = exif_data.get('EXIF:Make') or exif_data.get('IFD0:Make')
        if not metadata_dict.get('camera_model'):
            metadata_dict['camera_model'] = exif_data.get('EXIF:Model') or exif_data.get('IFD0:Model')
        if not metadata_dict.get('exposure_time'):
            metadata_dict['exposure_time'] = exif_data.get('EXIF:ExposureTime') or exif_data.get('EXIF:ShutterSpeedValue')
        if not metadata_dict.get('f_number'):
            metadata_dict['f_number'] = exif_data.get('EXIF:FNumber') or exif_data.get('EXIF:ApertureValue')
        if not metadata_dict.get('iso') and (exif_data.get('EXIF:ISO') or exif_data.get('EXIF:ISOSpeedRatings')):
            iso_val = exif_data.get('EXIF:ISO') or exif_data.get('EXIF:ISOSpeedRatings')
            try:
                metadata_dict['iso'] = int(iso_val) if isinstance(iso_val, (int, float, str)) else None
            except (ValueError, TypeError):
                pass
        if not metadata_dict.get('focal_length'):
            metadata_dict['focal_length'] = exif_data.get('EXIF:FocalLength') or exif_data.get('EXIF:FocalLengthIn35mmFormat')
    except (json.JSONDecodeError, AttributeError, TypeError, KeyError):
        pass  # 如果解析失败，忽略
    
    return metadata_dict


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
        
        # 过滤无效值（防御性编程：避免字符串 "undefined" 被当作有效值）
        if label and label.lower() in ('undefined', 'null', ''):
            label = None
        if rating is not None and rating <= 0:
            rating = None
        
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
                    metadata_dict = metadata.to_dict()
                    # 从 exif_data 中提取相机信息（如果存在）
                    metadata_dict = extract_camera_info_from_exif(metadata_dict)
                    result_item['metadata'] = metadata_dict
                results.append(result_item)
                
                if len(results) >= per_page:
                    break
        
        # 为所有结果添加 metadata（如果缺失）
        db = get_db()
        metadata_repo = MetadataRepository(db)
        for result_item in results:
            if 'metadata' not in result_item and 'image' in result_item:
                image_id = result_item['image'].get('id')
                if image_id:
                    metadata = metadata_repo.find_by_image_id(image_id)
                    if metadata:
                        metadata_dict = metadata.to_dict()
                        metadata_dict = extract_camera_info_from_exif(metadata_dict)
                        result_item['metadata'] = metadata_dict
        
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
        from utils.logger import get_logger
        logger = get_logger()
        logger.info(f"[API] 获取图像详情请求: image_id={image_id}")
        
        image_service = ServiceFactory.get_image_service()
        image_info = image_service.get_image_info(image_id)
        
        if not image_info:
            logger.warning(f"[API] 图像不存在: image_id={image_id}")
            return jsonify({
                'success': False,
                'error': 'Image not found'
            }), 404
        
        # 打印返回的数据结构（用于调试）
        logger.info(f"[API] 图像详情返回: image_id={image_id}, has_quality={bool(image_info.get('quality'))}, has_metadata={bool(image_info.get('metadata'))}")
        logger.info(f"[API] ai_analysis存在: {bool(image_info.get('ai_analysis'))}, 长度: {len(str(image_info.get('ai_analysis', ''))) if image_info.get('ai_analysis') else 0}")
        logger.info(f"[API] evaluations存在: {bool(image_info.get('evaluations'))}, 数量: {len(image_info.get('evaluations', [])) if image_info.get('evaluations') else 0}")
        if image_info.get('evaluations'):
            logger.info(f"[API] evaluations详情: {image_info.get('evaluations')}")
        
        return jsonify({
            'success': True,
            'data': image_info
        })
    except Exception as e:
        from utils.logger import get_logger
        logger = get_logger()
        logger.exception(f"[API] 获取图像详情失败: image_id={image_id}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/images/<int:image_id>/metadata', methods=['GET'])
def get_image_metadata(image_id: int):
    """获取图像的完整元数据（EXIF、GPS、XMP等）"""
    try:
        db = get_db()
        image_repo = ImageRepository(db)
        image = image_repo.find_by_id(image_id)
        
        if not image:
            return jsonify({
                'success': False,
                'error': 'Image not found'
            }), 404
        
        # 检查文件是否存在
        file_path = Path(image.file_path)
        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'Image file not found'
            }), 404
        
        # 读取完整元数据（自动检测项目内的ExifTool或系统PATH）
        from metadata.metadata_reader import MetadataReader
        
        reader = MetadataReader()  # 自动检测最佳ExifTool路径
        
        # 获取数据库中的元数据（降级方案）
        metadata_repo = MetadataRepository(db)
        db_metadata = metadata_repo.find_by_image_id(image_id)
        
        if not reader.is_available():
            # ExifTool不可用，返回数据库中的元数据和下载信息
            from utils.exiftool_manager import ExifToolManager
            manager = ExifToolManager()
            download_info = manager.get_download_info()
            
            # 组织数据库中的元数据
            fallback_metadata = {
                'file': {
                    'File:FileName': image.file_name,
                    'File:FileSize': image.file_size,
                    'File:FileType': image.format,
                    'File:Directory': str(Path(image.file_path).parent)
                },
                'exif': {},
                'gps': {},
                'xmp': {},
                'iptc': {},
                'other': {},
                'warning': {
                    'message': 'ExifTool不可用，仅显示数据库中的元数据',
                    'download_info': download_info,
                    'note': '请将ExifTool压缩包放到项目的exiftool/目录，系统会自动解压并使用',
                    'extract_note': '如果目录中已有压缩包但ExifTool不可用，请删除exiftool目录中的文件后重新解压压缩包'
                }
            }
            
            # 添加数据库中的XMP元数据
            if db_metadata:
                if db_metadata.xmp_rating:
                    fallback_metadata['xmp']['XMP-xmp:Rating'] = db_metadata.xmp_rating
                if db_metadata.xmp_label:
                    fallback_metadata['xmp']['XMP-xmp:Label'] = db_metadata.xmp_label
                if db_metadata.xmp_subjects:
                    fallback_metadata['xmp']['XMP-dc:Subject'] = db_metadata.xmp_subjects
                if db_metadata.xmp_description:
                    fallback_metadata['xmp']['XMP-dc:Description'] = db_metadata.xmp_description
            
            return jsonify({
                'success': True,
                'data': fallback_metadata,
                'warning': 'ExifTool不可用，仅显示数据库中的元数据。安装ExifTool后可查看完整元数据。'
            })
        
        # ExifTool可用，读取完整元数据
        from utils.logger import get_logger
        logger = get_logger()
        logger.info(f"开始读取图像元数据: image_id={image_id}, path={file_path}")
        
        metadata = reader.read_all(str(file_path))
        
        # 记录读取结果
        if metadata.get('error'):
            logger.warning(f"元数据读取失败: image_id={image_id}, error={metadata.get('error')}")
        else:
            categories = [k for k in metadata.keys() if k != 'error']
            total_items = sum(len(v) if isinstance(v, dict) else 0 for v in metadata.values())
            logger.info(f"元数据读取成功: image_id={image_id}, 类别数={len(categories)}, 总项数={total_items}")
        
        # 如果读取失败但有数据库元数据，合并显示
        if metadata.get('error') and db_metadata:
            metadata = {
                'file': metadata.get('file', {}),
                'exif': metadata.get('exif', {}),
                'gps': metadata.get('gps', {}),
                'xmp': metadata.get('xmp', {}),
                'iptc': metadata.get('iptc', {}),
                'other': metadata.get('other', {}),
                'warning': 'ExifTool读取部分失败，已合并数据库中的元数据'
            }
            # 合并数据库中的XMP元数据
            if db_metadata.xmp_rating:
                metadata['xmp']['XMP-xmp:Rating'] = db_metadata.xmp_rating
            if db_metadata.xmp_label:
                metadata['xmp']['XMP-xmp:Label'] = db_metadata.xmp_label
            if db_metadata.xmp_subjects:
                metadata['xmp']['XMP-dc:Subject'] = db_metadata.xmp_subjects
            if db_metadata.xmp_description:
                metadata['xmp']['XMP-dc:Description'] = db_metadata.xmp_description
        
        # 使用ensure_ascii=False确保中文字符正确显示
        response = jsonify({
            'success': True,
            'data': metadata
        })
        # 确保响应使用UTF-8编码
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        from utils.logger import get_logger
        logger = get_logger()
        logger.error(f"读取元数据失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/images/all-ids', methods=['GET'])
def get_all_image_ids():
    """获取所有图片的ID（用于批量分析，无分页限制）"""
    try:
        db = get_db()
        image_repo = ImageRepository(db)
        
        # 获取所有未删除的图片ID
        cursor = db.execute(
            "SELECT id FROM images WHERE deleted_at IS NULL ORDER BY id"
        )
        image_ids = [row['id'] for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'data': {
                'image_ids': image_ids,
                'count': len(image_ids)
            }
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
    """
    删除图像（软删除，移动到回收站）
    参考图片管理软件的删除逻辑：将文件从原文件夹移动到回收站
    """
    try:
        from utils.logger import get_logger
        logger = get_logger()
        
        db = get_db()
        image_repo = ImageRepository(db)
        
        # 检查图像是否存在
        image = image_repo.find_by_id(image_id)
        if not image:
            return jsonify({
                'success': False,
                'error': '图像不存在'
            }), 404
        
        if image.deleted_at:
            return jsonify({
                'success': False,
                'error': '图像已被删除'
            }), 400
        
        # 执行软删除（移动文件到回收站）
        success = image_repo.soft_delete(image_id)
        
        if success:
            logger.info(f"[删除] 图像已移动到回收站: image_id={image_id}")
            return jsonify({
                'success': True,
                'message': '图像已移动到回收站'
            })
        else:
            return jsonify({
                'success': False,
                'error': '删除失败'
            }), 500
    except Exception as e:
        from utils.logger import get_logger
        logger = get_logger()
        logger.error(f"[删除] 删除图像失败: image_id={image_id}, 错误: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/images/batch-delete', methods=['POST'])
def batch_delete_images():
    """
    批量删除图像（软删除，移动到回收站）
    参考图片管理软件的删除逻辑：将文件从原文件夹移动到回收站
    """
    try:
        from utils.logger import get_logger
        logger = get_logger()
        
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
        failed_count = 0
        errors = []
        
        for image_id in image_ids:
            try:
                if image_repo.soft_delete(image_id):
                    deleted_count += 1
                else:
                    failed_count += 1
                    errors.append(f"图像 {image_id} 不存在或已被删除")
            except Exception as e:
                failed_count += 1
                error_msg = f"图像 {image_id} 删除失败: {str(e)}"
                errors.append(error_msg)
                logger.error(f"[批量删除] {error_msg}", exc_info=True)
        
        message = f'成功删除 {deleted_count}/{len(image_ids)} 个图像'
        if failed_count > 0:
            message += f'，失败 {failed_count} 个'
        
        return jsonify({
            'success': deleted_count > 0,
            'message': message,
            'deleted_count': deleted_count,
            'failed_count': failed_count,
            'errors': errors if errors else None
        })
    except Exception as e:
        from utils.logger import get_logger
        logger = get_logger()
        logger.error(f"[批量删除] 批量删除失败: {str(e)}", exc_info=True)
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
    """
    永久删除图像（硬删除）
    参考图片管理软件的删除逻辑：删除文件 + 删除数据库记录 + 删除关联数据
    """
    try:
        from utils.logger import get_logger
        logger = get_logger()
        
        db = get_db()
        image_repo = ImageRepository(db)
        
        # 检查图像是否存在
        image = image_repo.find_by_id(image_id)
        if not image:
            return jsonify({
                'success': False,
                'error': '图像不存在'
            }), 404
        
        # 执行硬删除（删除文件 + 删除数据库记录）
        success = image_repo.hard_delete(image_id)
        
        if success:
            logger.info(f"[永久删除] 图像已永久删除: image_id={image_id}")
            return jsonify({
                'success': True,
                'message': '图像已永久删除'
            })
        else:
            return jsonify({
                'success': False,
                'error': '删除失败'
            }), 500
    except Exception as e:
        from utils.logger import get_logger
        logger = get_logger()
        logger.error(f"[永久删除] 永久删除图像失败: image_id={image_id}, 错误: {str(e)}", exc_info=True)
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

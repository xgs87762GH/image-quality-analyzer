"""统计相关API端点"""
from flask import jsonify
from . import api_bp
from services.service_factory import ServiceFactory


@api_bp.route('/stats', methods=['GET'])
def get_statistics():
    """获取统计信息"""
    try:
        quality_service = ServiceFactory.get_quality_service()
        image_service = ServiceFactory.get_image_service()
        
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

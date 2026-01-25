"""
AI相关API端点（高内聚：AI相关接口集中）
"""
from flask import jsonify, request
from flask_cors import cross_origin
from typing import Dict, Any

from . import api_bp
from services.service_factory import ServiceFactory
from utils.logger import get_logger

logger = get_logger()


@api_bp.route('/ai/ollama-models', methods=['GET', 'OPTIONS'])
@cross_origin(origins=['http://localhost:5173', 'http://127.0.0.1:5173'], 
              methods=['GET', 'OPTIONS'],
              allow_headers=['Content-Type'])
def get_ollama_models():
    """
    获取Ollama可用模型列表
    
    Query参数:
        ollama_base_url: Ollama API地址（可选，默认 http://localhost:11434）
    
    Returns:
        JSON响应，包含模型列表或错误信息
    """
    # 处理OPTIONS预检请求（cross_origin装饰器会自动处理，但为了确保兼容性，手动处理）
    if request.method == 'OPTIONS':
        origin = request.headers.get('Origin')
        if origin in ['http://localhost:5173', 'http://127.0.0.1:5173']:
            response = jsonify({})
            response.headers.add('Access-Control-Allow-Origin', origin)
            response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            return response
        return jsonify({}), 200
    
    try:
        ollama_base_url = request.args.get('ollama_base_url', 'http://localhost:11434')
        
        logger.info(f"[API] 获取Ollama模型列表: base_url={ollama_base_url}")
        
        # 创建临时AI分析器实例以获取模型列表
        ai_analyzer = ServiceFactory.create_ai_analyzer(
            model='ollama',
            ollama_base_url=ollama_base_url,
            ollama_model=''  # 临时模型名，仅用于获取列表
        )
        
        result = ai_analyzer.get_ollama_models()
        
        if result.get('success'):
            models = result.get('models', [])
            logger.info(f"[API] 成功获取Ollama模型列表: 数量={len(models)}")
            return jsonify({
                'success': True,
                'data': {
                    'models': models,
                    'count': len(models)
                }
            })
        else:
            error_msg = result.get('error', '获取模型列表失败')
            logger.warning(f"[API] 获取Ollama模型列表失败: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
            
    except Exception as e:
        logger.exception(f"[API] 获取Ollama模型列表异常: {e}")
        return jsonify({
            'success': False,
            'error': f'获取模型列表失败: {str(e)}'
        }), 500

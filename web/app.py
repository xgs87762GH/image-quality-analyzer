"""Flask应用主文件"""
from flask import Flask
import os

# 导入新的API蓝图（从web/api/__init__.py）
from web.api import api_bp
from web.views import views_bp

# 导入遗留API蓝图（从web/api_legacy.py，包含ollama/models等端点）
from web import api_legacy


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JSON_AS_ASCII'] = False  # 支持中文JSON
    
    # 初始化日志系统
    from utils.logger import setup_logger
    setup_logger("image_quality")
    setup_logger("flask")
    
    # 注册蓝图
    app.register_blueprint(api_bp)  # 新的模块化API（statistics, images等）
    
    # 注册遗留API蓝图（包含ollama/models等端点）
    try:
        legacy_bp = getattr(api_legacy, 'api_bp', None)
        if legacy_bp:
            app.register_blueprint(legacy_bp)
    except Exception as e:
        # 如果导入失败，记录但不中断启动
        from utils.logger import get_logger
        logger = get_logger()
        logger.warning(f"无法注册遗留API蓝图: {e}")
    
    app.register_blueprint(views_bp)
    
    # 图片服务路由（直接提供原图）
    from pathlib import Path
    from flask import send_file, send_from_directory
    
    @app.route('/images/<int:image_id>/file')
    def serve_image_file(image_id: int):
        """提供原图文件"""
        try:
            from database.connection import get_db
            from repositories.image_repository import ImageRepository
            
            db = get_db()
            image_repo = ImageRepository(db)
            image = image_repo.find_by_id(image_id)
            
            if not image:
                from flask import jsonify
                return jsonify({'error': '图片不存在'}), 404
            
            # 检查源文件是否存在
            image_path = Path(image.file_path)
            if not image_path.exists():
                from flask import jsonify
                return jsonify({'error': f'源文件不存在: {image.file_path}'}), 404
            
            # 直接发送原图文件
            return send_file(
                str(image_path.absolute()),
                mimetype=f'image/{image.format.lower() if image.format else "jpeg"}',
                as_attachment=False
            )
        except Exception as e:
            from flask import jsonify
            from utils.logger import get_logger
            logger = get_logger()
            logger.error(f"提供图片文件失败: {str(e)}", exc_info=True)
            return jsonify({'error': f'无法提供图片文件: {str(e)}'}), 500
    
    return app


if __name__ == '__main__':
    # 初始化数据库（如果未初始化）
    try:
        from database.connection import init_database
        init_database()
    except Exception:
        pass
    
    app = create_app()
    # 使用127.0.0.1避免Windows权限问题
    # 如需外部访问，可改为 host='0.0.0.0'，但可能需要管理员权限
    app.run(host='127.0.0.1', port=5000, debug=True)

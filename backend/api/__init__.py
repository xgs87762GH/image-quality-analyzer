"""Web API模块 - 按功能拆分的API端点"""
from flask import Blueprint

# 创建主蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

# 导入所有子模块（注册路由）
from . import statistics, images, ai

# 注意：其他端点（analysis, models, directories, system）暂时保留在 api_legacy 中
# 后续可逐步迁移到本模块

__all__ = ['api_bp']

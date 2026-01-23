"""Web视图路由"""
from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)


@views_bp.route('/')
def index():
    """首页 - 图像列表"""
    return render_template('index.html')


@views_bp.route('/image/<int:image_id>')
def image_detail(image_id: int):
    """图像详情页"""
    return render_template('image_detail.html', image_id=image_id)


@views_bp.route('/stats')
def statistics():
    """统计页面"""
    return render_template('stats.html')


@views_bp.route('/duplicates')
def duplicates():
    """重复图像页面"""
    return render_template('duplicates.html')


@views_bp.route('/trash')
def trash():
    """回收站页面"""
    return render_template('trash.html')


@views_bp.route('/system')
def system_info():
    """系统信息页面"""
    return render_template('system_info.html')

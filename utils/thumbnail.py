"""
缩略图生成工具（已废弃）

注意：此模块已废弃，系统现在直接使用原图。
保留此文件仅用于向后兼容，新代码不应使用此模块。
"""
import os
from pathlib import Path
from typing import Optional
from PIL import Image as PILImage

from config.settings import get_settings


def generate_thumbnail(image_path: str, 
                      thumbnail_dir: str = "thumbnails",
                      max_size: tuple = (200, 200),
                      quality: int = 85) -> Optional[str]:
    """
    生成图像缩略图（已废弃）
    
    注意：此函数已废弃，系统现在直接使用原图。
    返回None表示不再生成缩略图。
    
    Args:
        image_path: 原始图像路径
        thumbnail_dir: 缩略图保存目录（已废弃）
        max_size: 最大尺寸 (width, height)（已废弃）
        quality: JPEG质量 (1-100)（已废弃）
        
    Returns:
        None（不再生成缩略图）
    """
    # 已废弃：不再生成缩略图，直接使用原图
    return None


def get_thumbnail_url(thumbnail_path: Optional[str]) -> Optional[str]:
    """
    获取缩略图URL（用于Web显示）
    
    Args:
        thumbnail_path: 缩略图路径
        
    Returns:
        缩略图URL
    """
    if not thumbnail_path:
        return None
    
    thumb_path = Path(thumbnail_path)
    if not thumb_path.exists():
        return None
    
    # 返回相对于项目根目录的路径，用于Web访问
    # 实际使用时需要配置Web服务器提供静态文件服务
    return f"/thumbnails/{thumb_path.name}"

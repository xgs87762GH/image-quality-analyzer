#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复现有图像的缩略图路径"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.encoding import setup_console_encoding
from database.connection import get_db
from repositories.image_repository import ImageRepository
from utils.thumbnail import generate_thumbnail

setup_console_encoding()

if __name__ == '__main__':
    print("正在修复缩略图路径...")
    
    db = get_db()
    repo = ImageRepository(db)
    
    # 获取所有图像
    images = repo.list_all(limit=10000, include_deleted=False)
    
    print(f"找到 {len(images)} 个图像")
    
    fixed_count = 0
    for img in images:
        if not img.thumbnail_path:
            # 生成缩略图
            thumbnail_path = generate_thumbnail(img.file_path)
            if thumbnail_path:
                img.thumbnail_path = thumbnail_path
                repo.update(img)
                fixed_count += 1
                print(f"✓ 已修复: {img.file_name}")
    
    print(f"\n修复完成！共修复 {fixed_count} 个图像")

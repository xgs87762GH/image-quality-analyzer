#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库迁移脚本"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection import get_db
import importlib.util
from pathlib import Path
from utils.encoding import setup_console_encoding

setup_console_encoding()

def load_migration(module_name, file_path):
    """动态加载迁移模块"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

if __name__ == "__main__":
    print("正在执行数据库迁移...")
    try:
        db = get_db()
        
        # 执行迁移 002
        migrations_dir = Path(__file__).parent.parent / "database" / "migrations"
        migration_002 = load_migration("migration_002", migrations_dir / "002_add_thumbnail_and_deleted.py")
        print("执行迁移 002: 添加缩略图和删除字段...")
        migration_002.up(db)
        
        # 执行迁移 003
        migration_003 = load_migration("migration_003", migrations_dir / "003_add_original_path.py")
        print("执行迁移 003: 添加原路径字段...")
        migration_003.up(db)
        
        # 执行迁移 004
        migration_004 = load_migration("migration_004", migrations_dir / "004_add_ai_analysis_fields.py")
        print("执行迁移 004: 添加AI分析结果和评估结果字段...")
        migration_004.up(db)
        
        # 执行迁移 005
        migration_005 = load_migration("migration_005", migrations_dir / "005_add_evaluations_array.py")
        print("执行迁移 005: 添加评估问题数组字段...")
        migration_005.up(db)
        
        print("数据库迁移完成！")
    except Exception as e:
        print(f"数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

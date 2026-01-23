#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""初始化数据库脚本"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection import get_db, init_database
from utils.encoding import setup_console_encoding

setup_console_encoding()

if __name__ == "__main__":
    print("正在初始化数据库...")
    try:
        init_database()
        print("数据库初始化完成！")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启动Web界面"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.encoding import setup_console_encoding
from database.connection import init_database
from web.app import create_app

setup_console_encoding()

if __name__ == '__main__':
    # 初始化数据库（如果未初始化）
    try:
        init_database()
        print("数据库已初始化")
    except Exception as e:
        print(f"数据库初始化警告: {e}")
    
    app = create_app()
    print("\n" + "="*50)
    print("Web界面已启动！")
    print("访问地址: http://localhost:5000")
    print("="*50 + "\n")
    
    # Windows权限问题解决方案：
    # 1. 使用127.0.0.1而不是0.0.0.0（已设置）
    # 2. 如果仍有问题，尝试以管理员权限运行
    # 3. 或检查端口5000是否被占用
    try:
        app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
    except OSError as e:
        if "以一种访问权限不允许的方式做了一个访问套接字的尝试" in str(e) or "permission denied" in str(e).lower():
            print("\n" + "="*50)
            print("⚠️  端口权限错误！")
            print("="*50)
            print("\n解决方案：")
            print("1. 以管理员权限运行PowerShell，然后重新运行此命令")
            print("2. 检查端口5000是否被占用：")
            print("   netstat -ano | findstr :5000")
            print("3. 如果端口被占用，结束占用进程或使用其他端口")
            print("\n详细说明请查看: docs/getting-started/STARTUP_GUIDE.md")
            print("="*50 + "\n")
            sys.exit(1)
        else:
            raise

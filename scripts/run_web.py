#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启动后端 API 服务（Flask + WebSocket）"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.encoding import setup_console_encoding
from database.connection import init_database
from backend.app import create_app
from utils.exiftool_manager import ExifToolManager

setup_console_encoding()

if __name__ == '__main__':
    # 初始化数据库（如果未初始化）
    try:
        init_database()
        print("数据库已初始化")
    except Exception as e:
        print(f"数据库初始化警告: {e}")
    
    # 检查并自动解压ExifTool（如果目录中有压缩包）
    print("\n检查ExifTool...")
    manager = ExifToolManager()
    if not manager.is_available():
        if manager._has_executable() and manager._is_incomplete():
            print("⚠ ExifTool安装不完整（缺少依赖文件）")
            print("  请重新下载压缩包到 exiftool/ 目录，系统会自动解压")
            print("  下载地址: https://exiftool.org/")
            print("  或者手动解压压缩包，确保包含 exiftool_files 目录")
        else:
            print("ExifTool未找到，正在检查压缩包...")
            extract_result = manager.extract_exiftool()
            
            # 解压后等待一小段时间，确保文件系统更新
            import time
            time.sleep(0.2)
            
            # 重新检测（解压后可能需要重新检测）
            manager._detect_exiftool()
            
            # 解压后重新检查可用性
            if manager.is_available():
                exiftool_path = manager.get_exiftool_path()
                print(f"✓ ExifTool已成功解压并安装: {exiftool_path}")
            else:
                # 详细诊断
                if manager._has_executable():
                    if manager._is_incomplete():
                        print("⚠ ExifTool安装不完整（缺少依赖文件 exiftool_files）")
                        print("  请重新下载压缩包到 exiftool/ 目录，系统会自动解压")
                    else:
                        print("⚠ ExifTool文件存在但无法运行")
                        print(f"  文件路径: {manager.get_exiftool_path()}")
                        print("  可能原因: 文件损坏或权限问题")
                        print("  提示: 请运行 'python tests/diagnose_exiftool.py' 进行详细诊断")
                else:
                    print("⚠ ExifTool不可用，请手动下载压缩包到 exiftool/ 目录")
                print("  下载地址: https://exiftool.org/")
    else:
        exiftool_path = manager.get_exiftool_path()
        print(f"✓ ExifTool已就绪: {exiftool_path}")
    
    app = create_app()
    import backend.websocket
    socketio = backend.websocket.socketio
    print("\n" + "="*50)
    print("后端 API 已启动！（含 WebSocket）")
    print("访问地址: http://localhost:5000")
    print("="*50 + "\n")

    # Windows权限问题解决方案：
    # 1. 使用127.0.0.1而不是0.0.0.0（已设置）
    # 2. 如果仍有问题，尝试以管理员权限运行
    # 3. 或检查端口5000是否被占用
    try:
        socketio.run(app, host='127.0.0.1', port=5000, debug=True, use_reloader=False)
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

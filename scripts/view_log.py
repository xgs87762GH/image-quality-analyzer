#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看日志文件（使用UTF-8编码）"""
import sys
from pathlib import Path

# 设置控制台编码
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

def view_log(log_file='logs/image_quality.log', lines=50):
    """查看日志文件"""
    log_path = Path(log_file)
    
    if not log_path.exists():
        print(f"日志文件不存在: {log_path}")
        return
    
    try:
        # 尝试使用UTF-8-sig读取（支持BOM）
        with open(log_path, 'r', encoding='utf-8-sig') as f:
            all_lines = f.readlines()
            
        # 显示最后N行
        print(f"\n{'='*60}")
        print(f"日志文件: {log_path}")
        print(f"总行数: {len(all_lines)}")
        print(f"显示最后 {min(lines, len(all_lines))} 行:")
        print('='*60)
        
        for line in all_lines[-lines:]:
            print(line.rstrip())
            
    except Exception as e:
        print(f"读取日志文件失败: {e}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='查看日志文件')
    parser.add_argument('--file', default='logs/image_quality.log', help='日志文件路径')
    parser.add_argument('--lines', type=int, default=50, help='显示行数')
    args = parser.parse_args()
    
    view_log(args.file, args.lines)

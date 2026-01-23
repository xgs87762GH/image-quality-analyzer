"""控制台编码处理工具"""
import sys
import io


def setup_console_encoding():
    """设置控制台编码为UTF-8（Windows平台）"""
    if sys.platform == 'win32':
        try:
            # 尝试设置UTF-8编码
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except (AttributeError, ValueError):
            # 如果reconfigure不可用，使用TextIOWrapper
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, 
                encoding='utf-8', 
                errors='replace'
            )
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, 
                encoding='utf-8', 
                errors='replace'
            )

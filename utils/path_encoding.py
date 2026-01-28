"""路径编码处理工具 - 处理 Windows 中文路径编码问题（高内聚）"""
import platform
import os
import subprocess
import ctypes
from ctypes import wintypes
from pathlib import Path
from typing import Optional
from utils.logger import get_logger


class PathEncoder:
    """
    路径编码处理器
    
    职责：
    - 统一处理 Windows 上的路径编码问题
    - 确保路径可以正确传递给 subprocess
    - 提供路径规范化功能
    
    设计原则：
    - 高内聚：所有路径编码处理逻辑集中在此
    - 低耦合：不依赖外部库（如 win32api），使用 Python 标准库
    """
    
    def __init__(self):
        """初始化路径编码器"""
        self._logger = get_logger()
        self._is_windows = platform.system() == 'Windows'
    
    def normalize_path(self, path: str, use_short_path: bool = False) -> str:
        """
        规范化路径，确保可以正确传递给 subprocess
        
        Args:
            path: 原始路径（可能包含中文）
            use_short_path: 是否使用短路径名（8.3格式），用于 ExifTool 等工具
            
        Returns:
            规范化后的路径
        """
        if not isinstance(path, str):
            path = str(path)
        
        # Python 3 的 subprocess 原生支持 Unicode
        # 直接使用 Path 对象规范化路径，然后转换为字符串
        try:
            path_obj = Path(path)
            # 使用 resolve() 获取绝对路径，确保路径格式正确
            if path_obj.is_absolute():
                normalized = str(path_obj.resolve())
            else:
                # 相对路径，转换为绝对路径
                normalized = str(Path(path).resolve())
            
            # 验证路径编码（确保是有效的 UTF-8）
            normalized.encode('utf-8')
            
            # 如果需要使用短路径名（用于 ExifTool 等工具）
            if use_short_path and self._is_windows:
                self._logger.info(f"尝试获取短路径名: {normalized[:60]}...")
                short_path = self._get_short_path(normalized)
                if short_path != normalized:
                    self._logger.info(f"使用短路径名成功: {normalized[:60]}... -> {short_path[:60]}...")
                    return short_path
                else:
                    self._logger.warning(f"短路径名获取失败，返回原路径: {normalized[:60]}...")
            
            return normalized
        except (OSError, ValueError) as e:
            # 如果路径解析失败，记录警告但返回原路径
            self._logger.debug(f"路径规范化失败: {path}, 错误: {e}")
            return path
        except UnicodeEncodeError as e:
            # 如果编码失败，记录错误
            self._logger.warning(f"路径编码验证失败: {path}, 错误: {e}")
            return path
    
    def _get_short_path(self, long_path: str) -> str:
        """
        获取 Windows 短路径名（8.3格式），用于避免中文路径编码问题
        
        使用 Windows API GetShortPathNameW（Unicode 版本），这是最可靠的方法
        
        Args:
            long_path: 长路径（可能包含中文）
            
        Returns:
            短路径名，如果获取失败则返回原路径或长路径前缀格式
        """
        if not self._is_windows:
            return long_path
        
        # 方法1：使用 Windows API GetShortPathNameW（最可靠，无需外部依赖）
        try:
            # 首先转换为绝对路径
            abs_path = os.path.abspath(long_path)
            
            # 使用 Windows API GetShortPathNameW（Unicode 版本）
            kernel32 = ctypes.windll.kernel32
            GetShortPathNameW = kernel32.GetShortPathNameW
            GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
            GetShortPathNameW.restype = wintypes.DWORD
            
            # 第一次调用获取缓冲区大小
            buffer_size = GetShortPathNameW(abs_path, None, 0)
            if buffer_size == 0:
                error_code = ctypes.get_last_error()
                if error_code != 0:
                    self._logger.warning(f"GetShortPathNameW 获取缓冲区大小失败: 错误码={error_code}, 路径={abs_path[:50]}...")
                else:
                    # 文件可能不存在或没有短路径名，尝试使用长路径前缀
                    self._logger.debug(f"无法获取短路径名（可能文件不存在或系统禁用），尝试使用长路径前缀: {abs_path[:50]}...")
                    if not abs_path.startswith('\\\\?\\'):
                        return '\\\\?\\' + abs_path
                    return abs_path
            
            # 第二次调用获取实际短路径
            buffer = ctypes.create_unicode_buffer(buffer_size)
            result = GetShortPathNameW(abs_path, buffer, buffer_size)
            if result == 0:
                error_code = ctypes.get_last_error()
                self._logger.warning(f"GetShortPathNameW 获取短路径失败: 错误码={error_code}, 路径={abs_path[:50]}...")
                # 失败时尝试使用长路径前缀
                if not abs_path.startswith('\\\\?\\'):
                    return '\\\\?\\' + abs_path
                return abs_path
            
            short_path = buffer.value
            if short_path and os.path.exists(short_path):
                self._logger.info(f"Windows API 获取短路径成功: {abs_path[:50]}... -> {short_path[:50]}...")
                return short_path
            else:
                self._logger.warning(f"Windows API 返回的短路径不存在: {short_path}")
        except Exception as e:
            self._logger.error(
                f"Windows API 获取短路径异常: {long_path[:50]}..., "
                f"错误类型: {type(e).__name__}, "
                f"错误信息: {str(e)}",
                exc_info=True
            )
        
        # 方法2：尝试使用 win32api（如果可用，作为备选）
        try:
            import win32api
            self._logger.info(f"尝试使用 win32api 获取短路径: {long_path[:50]}...")
            short_path = win32api.GetShortPathName(long_path)
            if short_path and os.path.exists(short_path):
                self._logger.info(f"win32api 获取短路径成功: {long_path[:50]}... -> {short_path[:50]}...")
                return short_path
        except ImportError:
            # win32api 不可用，继续尝试其他方法
            pass
        except Exception as e:
            self._logger.debug(f"win32api 获取短路径失败: {e}")
        
        # 方法3：使用 PowerShell（最后备选方案）
        try:
            self._logger.info(f"尝试使用 PowerShell 获取短路径: {long_path[:50]}...")
            escaped_path = long_path.replace("'", "''")
            ps_command = f"(New-Object -ComObject Scripting.FileSystemObject).GetFile('{escaped_path}').ShortPath"
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', ps_command],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                short_path = result.stdout.strip().strip('"').strip("'")
                if short_path and os.path.exists(short_path):
                    self._logger.info(f"PowerShell 获取短路径成功: {long_path[:50]}... -> {short_path[:50]}...")
                    return short_path
        except Exception as e:
            self._logger.debug(f"PowerShell 获取短路径失败: {e}")
        
        # 如果所有方法都失败，尝试使用长路径前缀（\\?\）
        abs_path = os.path.abspath(long_path)
        if not abs_path.startswith('\\\\?\\'):
            self._logger.warning(f"所有短路径获取方法失败，使用长路径前缀: {long_path[:50]}...")
            return '\\\\?\\' + abs_path
        
        # 如果已经使用了长路径前缀，直接返回
        self._logger.error(f"无法获取短路径名，将使用原路径（可能导致编码问题）: {long_path[:50]}...")
        return long_path
    
    def is_file_path(self, arg: str) -> bool:
        """
        判断参数是否是文件路径
        
        Args:
            arg: 待检查的参数
            
        Returns:
            如果是文件路径返回 True，否则返回 False
        """
        if not isinstance(arg, str) or len(arg) == 0:
            return False
        
        # 检查路径特征
        has_drive = len(arg) > 1 and arg[1] == ':'  # Windows 驱动器号
        has_slash = '/' in arg or '\\' in arg  # 包含斜杠
        is_absolute = arg.startswith('/')  # Unix 绝对路径
        
        return has_drive or (has_slash and len(arg) > 3) or is_absolute
    
    def prepare_subprocess_env(self, base_env: Optional[dict] = None) -> dict:
        """
        准备 subprocess 环境变量，确保 UTF-8 编码
        
        Args:
            base_env: 基础环境变量字典（可选）
            
        Returns:
            配置好的环境变量字典
        """
        env = os.environ.copy()
        if base_env:
            env.update(base_env)
        
        if self._is_windows:
            # Windows 上设置 UTF-8 编码环境变量
            # 这确保子进程使用 UTF-8 编码处理输入输出
            env['PYTHONIOENCODING'] = 'utf-8'
            # 设置 ExifTool 相关的编码环境变量（如果 ExifTool 支持）
            # ExifTool 使用 -charset 参数，但环境变量可以作为补充
        
        return env

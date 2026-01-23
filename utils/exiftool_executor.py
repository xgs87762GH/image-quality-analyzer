"""ExifTool 执行器 - 统一处理 ExifTool 命令执行（高内聚、低耦合）"""
import subprocess
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any
from utils.exiftool_manager import ExifToolManager
from utils.logger import get_logger


class ExifToolExecutor:
    """
    ExifTool 执行器
    
    职责：
    - 统一管理 ExifTool 命令执行
    - 处理工作目录设置
    - 处理超时和异常
    - 记录日志
    
    设计原则：
    - 高内聚：所有 ExifTool 执行逻辑集中在此
    - 低耦合：其他模块只依赖此执行器，不直接操作 ExifTool
    """
    
    def __init__(self):
        """初始化执行器"""
        self._manager = ExifToolManager()
        self._exiftool_path = self._manager.get_exiftool_path()
        self._exiftool_dir = self._manager.exiftool_dir
        self._logger = get_logger()
        self._available = self._check_availability()
    
    def is_available(self) -> bool:
        """检查 ExifTool 是否可用"""
        return self._available
    
    def get_path(self) -> Optional[str]:
        """获取 ExifTool 路径"""
        return str(self._exiftool_path) if self._exiftool_path else None
    
    def _check_availability(self) -> bool:
        """检查 ExifTool 可用性"""
        if not self._exiftool_path:
            return False
        
        try:
            # 直接执行检查，不通过 _run_command（避免循环依赖）
            cmd = [str(self._exiftool_path), "-ver"]
            cwd = self._get_working_directory()
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _get_working_directory(self) -> str:
        """获取工作目录（确保能找到 DLL 文件）"""
        if self._exiftool_path:
            exe_path = Path(self._exiftool_path)
            if exe_path.is_absolute() and exe_path.parent.name == 'exiftool':
                return str(exe_path.parent)
        return str(self._exiftool_dir)
    
    def _run_command(self, args: List[str], check: bool = True, timeout: int = 30) -> Dict[str, Any]:
        """
        执行 ExifTool 命令
        
        Args:
            args: ExifTool 命令参数列表
            check: 是否检查返回码（默认 True）
            timeout: 超时时间（秒）
        
        Returns:
            包含 success, returncode, stdout, stderr 的字典
        """
        if not self._available:
            return {
                'success': False,
                'error': 'ExifTool不可用',
                'returncode': -1,
                'stdout': '',
                'stderr': ''
            }
        
        if not self._exiftool_path:
            return {
                'success': False,
                'error': 'ExifTool路径未找到',
                'returncode': -1,
                'stdout': '',
                'stderr': ''
            }
        
        # 处理文件路径编码（Windows中文路径问题）
        processed_args = []
        for arg in args:
            # 如果是文件路径，确保使用正确的编码
            if isinstance(arg, str) and (arg.startswith('/') or ':' in arg or '\\' in arg):
                # 文件路径，确保是有效的UTF-8字符串
                try:
                    # 尝试编码/解码以确保是有效的UTF-8
                    arg.encode('utf-8').decode('utf-8')
                    processed_args.append(arg)
                except (UnicodeEncodeError, UnicodeDecodeError):
                    # 如果编码失败，尝试修复
                    processed_args.append(arg.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
            else:
                processed_args.append(arg)
        
        cmd = [str(self._exiftool_path)] + processed_args
        cwd = self._get_working_directory()
        
        try:
            # Windows上，subprocess.run需要正确处理中文路径
            # 使用shell=False，但确保路径是有效的
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',  # 明确指定UTF-8编码
                errors='replace',  # 遇到无法解码的字符时替换为占位符
                timeout=timeout,
                cwd=cwd,
                stdin=subprocess.DEVNULL,  # 避免等待输入
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            
            success = result.returncode == 0 if check else True
            
            return {
                'success': success,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except subprocess.TimeoutExpired as e:
            self._logger.error(f"ExifTool 执行超时: {' '.join(cmd)}")
            return {
                'success': False,
                'error': f'执行超时: {timeout}秒',
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }
        except Exception as e:
            self._logger.error(f"ExifTool 执行异常: {' '.join(cmd)}, 错误: {e}")
            return {
                'success': False,
                'error': f'执行异常: {str(e)}',
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }
    
    def execute(self, args: List[str], timeout: int = 30) -> Dict[str, Any]:
        """
        执行 ExifTool 命令（公共接口）
        
        Args:
            args: ExifTool 命令参数列表
            timeout: 超时时间（秒）
        
        Returns:
            执行结果字典
        """
        result = self._run_command(args, check=True, timeout=timeout)
        
        if not result['success']:
            self._logger.warning(
                f"ExifTool 执行失败: {' '.join(args)}, "
                f"返回码: {result['returncode']}, "
                f"错误: {result.get('error', result['stderr'])}"
            )
        
        return result

"""ExifTool 执行器 - 统一处理 ExifTool 命令执行（高内聚、低耦合）"""
import subprocess
import platform
import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from utils.exiftool_manager import ExifToolManager
from utils.logger import get_logger
from utils.path_encoding import PathEncoder


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
        self._path_encoder = PathEncoder()  # 路径编码处理器（依赖注入）
        self._available = self._check_availability()
        self._exiftool_version = self._get_version()  # 获取 ExifTool 版本
        self._supports_long_path = self._check_long_path_support()  # 检查是否支持长路径
    
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
    
    def _get_version(self) -> Optional[str]:
        """获取 ExifTool 版本号"""
        if not self._available:
            return None
        
        try:
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
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def _check_long_path_support(self) -> bool:
        """
        检查是否支持 Windows 长路径
        
        Returns:
            如果 ExifTool 版本 >= 13.01 且是 Windows 系统，返回 True
        """
        if platform.system() != 'Windows':
            return False
        
        if not self._exiftool_version:
            return False
        
        try:
            # 解析版本号（格式如 "13.01" 或 "13.1"）
            version_parts = self._exiftool_version.split('.')
            major = int(version_parts[0])
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            
            # ExifTool 13.01+ 支持 WindowsLongPath API
            return major > 13 or (major == 13 and minor >= 1)
        except (ValueError, IndexError):
            return False
    
    
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
        
        # 处理参数编码（Windows中文路径问题）
        # 核心问题：Windows 命令行参数编码机制导致中文路径被错误编码
        # 最可靠的解决方案：使用 ExifTool 的参数文件功能（-@ 参数）
        # 这样可以完全绕过命令行参数编码问题，ExifTool 会自行以 UTF-8 读取文件
        
        # 创建参数文件内容（使用 UTF-8 编码）
        argfile_content = []
        
        # 添加字符集配置（确保 UTF-8 处理）
        # 注意：这些参数已经在 xmp_writer.py 中添加，但为了确保，这里也添加
        # 如果 args 中已经包含，ExifTool 会使用最后一个
        argfile_content.append("-charset")
        argfile_content.append("filename=utf8")
        argfile_content.append("-charset")
        argfile_content.append("utf8")
        
        # 如果支持 Windows 长路径，添加 API 参数
        if self._supports_long_path and platform.system() == 'Windows':
            has_api_param = any(arg.startswith('-api') for arg in args)
            if not has_api_param:
                argfile_content.append("-api")
                argfile_content.append("WindowsLongPath")
                self._logger.debug(f"添加 WindowsLongPath API 参数（ExifTool 版本: {self._exiftool_version}）")
        
        # 处理原始参数
        for arg in args:
            if isinstance(arg, str):
                # 如果是文件路径，规范化路径
                if self._path_encoder.is_file_path(arg):
                    self._logger.info(f"检测到文件路径，开始规范化: {arg[:60]}...")
                    try:
                        # 对于 ExifTool，尝试使用短路径名以确保兼容性
                        normalized = self._path_encoder.normalize_path(arg, use_short_path=True)
                        
                        # 记录路径转换信息
                        if normalized != arg:
                            self._logger.info(f"路径转换成功: {arg[:60]}... -> {normalized[:60]}...")
                        else:
                            self._logger.debug(f"路径未转换（可能已使用长路径前缀）: {arg[:60]}...")
                        
                        # 添加到参数文件（路径中的空格和特殊字符会被 ExifTool 正确处理）
                        argfile_content.append(normalized)
                    except Exception as e:
                        # 规范化失败，使用原参数
                        self._logger.error(
                            f"路径规范化失败，使用原参数: {arg[:50]}..., "
                            f"错误类型: {type(e).__name__}, "
                            f"错误信息: {str(e)}",
                            exc_info=True
                        )
                        argfile_content.append(arg)
                else:
                    # 非文件路径参数，直接添加
                    # 如果包含空格或引号，ExifTool 在参数文件中会正确处理
                    argfile_content.append(arg)
            else:
                # 非字符串参数转换为字符串
                argfile_content.append(str(arg))
        
        # 创建临时参数文件
        argfile_path = None
        try:
            # 使用系统临时目录，确保 ExifTool 有权限访问
            temp_dir = tempfile.gettempdir()
            argfile_path = os.path.join(temp_dir, f"exiftool_args_{uuid.uuid4().hex}.txt")
            
            # 使用 UTF-8 写入参数文件（带 BOM，确保 Windows 正确识别）
            # ExifTool 会以 UTF-8 读取文件，完全绕过命令行编码问题
            with open(argfile_path, 'w', encoding='utf-8-sig') as f:
                f.write('\n'.join(argfile_content))
            
            self._logger.debug(f"创建参数文件: {argfile_path}")
            self._logger.debug(f"参数文件内容预览（前10行）: {chr(10).join(argfile_content[:10])}")
            self._logger.debug(f"参数文件总行数: {len(argfile_content)}")
            
            # 构建命令：exiftool -@ argfile.txt
            # 使用 -@ 参数文件方式，完全绕过命令行参数编码问题
            cmd = [str(self._exiftool_path), "-@", argfile_path]
            cwd = self._get_working_directory()
            env = self._path_encoder.prepare_subprocess_env()
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,  # 使用文本模式
                encoding='utf-8',  # 明确指定 UTF-8 编码处理输出
                errors='replace',  # 遇到无法解码的字符时替换为占位符（防御性编程）
                timeout=timeout,
                cwd=cwd,
                env=env,  # 使用配置好的环境变量
                stdin=subprocess.DEVNULL,  # 避免等待输入
                shell=False,  # 不使用 shell，直接使用 CreateProcessW API
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            
            success = result.returncode == 0 if check else True
            
            # 如果执行失败，记录详细信息
            if not success:
                self._logger.warning(
                    f"ExifTool 执行失败: 返回码: {result.returncode}, "
                    f"stdout: {result.stdout[:200] if result.stdout else '(空)'}, "
                    f"stderr: {result.stderr[:200] if result.stderr else '(空)'}"
                )
            
            return {
                'success': success,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired as e:
            self._logger.error(
                f"ExifTool 执行超时: 参数文件: {argfile_path if argfile_path else '(未创建)'}, "
                f"超时时间: {timeout}秒",
                exc_info=True
            )
            return {
                'success': False,
                'error': f'执行超时: {timeout}秒',
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }
        except Exception as e:
            # 打印完整的异常信息，包括堆栈跟踪
            self._logger.error(
                f"ExifTool 执行异常: 参数文件: {argfile_path if argfile_path else '(未创建)'}, "
                f"错误类型: {type(e).__name__}, "
                f"错误信息: {str(e)}",
                exc_info=True
            )
            return {
                'success': False,
                'error': f'执行异常: {type(e).__name__}: {str(e)}',
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }
        finally:
            # 确保清理临时参数文件
            if argfile_path and os.path.exists(argfile_path):
                try:
                    os.unlink(argfile_path)
                    self._logger.debug(f"已清理临时参数文件: {argfile_path}")
                except Exception as e:
                    self._logger.warning(f"清理临时参数文件失败: {argfile_path}, 错误: {e}")
    
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

"""
回收站服务（高内聚：回收站相关功能集中）
参考 digiKam 实现方式：文件移动 + 数据库标记
跨平台支持：Windows、macOS、Linux
"""
import time
import platform
import os
from pathlib import Path
from typing import Optional, Tuple
from shutil import move
from datetime import datetime

from utils.logger import get_logger
from config.settings import get_settings


class TrashManager:
    """
    回收站管理器（跨平台支持）
    
    职责：
    - 管理文件移动到回收站
    - 管理文件从回收站恢复
    - 计算回收站路径（保留目录结构）
    - 处理文件冲突（重名文件）
    - 跨平台路径处理（Windows/macOS/Linux）
    
    设计原则：
    - 高内聚：所有回收站操作集中在此类
    - 低耦合：通过依赖注入使用配置和数据库
    """
    
    def __init__(self):
        """初始化回收站管理器"""
        self._logger = get_logger()
        self._settings = get_settings()
        self._platform = platform.system().lower()
        self._trash_dir = Path(self._settings.trash.trash_dir).resolve()
        self._preserve_structure = self._settings.trash.preserve_structure
        
        # 确保回收站目录存在（跨平台）
        self._ensure_trash_dir_exists()
        self._logger.debug(f"[回收站] 平台: {self._platform}, 回收站目录: {self._trash_dir}")
    
    def _ensure_trash_dir_exists(self) -> None:
        """
        确保回收站目录存在（跨平台兼容）
        
        Raises:
            OSError: 如果无法创建目录
        """
        try:
            self._trash_dir.mkdir(parents=True, exist_ok=True)
            # 验证目录权限（Linux/macOS）
            if self._platform != 'windows':
                if not os.access(self._trash_dir, os.W_OK):
                    raise PermissionError(f"回收站目录无写权限: {self._trash_dir}")
        except PermissionError:
            self._logger.error(f"[回收站] 无法创建回收站目录（权限不足）: {self._trash_dir}", exc_info=True)
            raise
        except Exception as e:
            self._logger.error(f"[回收站] 创建回收站目录失败: {self._trash_dir}, 错误: {e}", exc_info=True)
            raise
    
    def get_trash_dir(self) -> Path:
        """
        获取回收站目录路径
        
        Returns:
            回收站目录的 Path 对象
        """
        return self._trash_dir
    
    def calculate_trash_path(self, source_path: Path) -> Path:
        """
        计算文件在回收站中的路径（保留目录结构，跨平台）
        
        Args:
            source_path: 源文件路径
            
        Returns:
            回收站中的目标路径
        """
        source_path = source_path.resolve()
        
        if not self._preserve_structure:
            # 不保留结构，直接放到回收站根目录
            return self._trash_dir / source_path.name
        
        try:
            # 保留目录结构（跨平台处理）
            path_parts = source_path.parts
            self._logger.debug(f"[回收站] 路径分解: {path_parts}, 平台: {self._platform}")
            
            if len(path_parts) > 1:
                relative_parts = self._extract_relative_parts(path_parts)
                self._logger.debug(f"[回收站] 相对路径部分: {relative_parts}")
            else:
                # 只有文件名
                relative_parts = [source_path.name]
                self._logger.debug(f"[回收站] 仅文件名，相对路径: {relative_parts}")
            
            trash_path = self._trash_dir / Path(*relative_parts)
            self._logger.info(f"[回收站] 计算出的回收站路径: {trash_path}")
            return trash_path
            
        except Exception as e:
            self._logger.warning(f"[回收站] 计算回收站路径失败，使用文件名: {e}", exc_info=True)
            # 如果计算失败，使用文件名
            return self._trash_dir / source_path.name
    
    def _extract_relative_parts(self, path_parts: tuple) -> list:
        """
        提取相对路径部分（跨平台）
        
        Args:
            path_parts: 路径部分元组
            
        Returns:
            相对路径部分列表
        """
        if self._platform == 'windows':
            # Windows: 处理驱动器号
            first_part = path_parts[0]
            if self._is_windows_drive(first_part):
                # 提取驱动器号
                drive_letter = first_part[0] if len(first_part) >= 2 else first_part[0]
                drive_name = f"{drive_letter}_"
                # 保留从第一个目录开始的结构（跳过驱动器号部分）
                relative_parts = list(path_parts[1:])
                relative_parts = [drive_name] + relative_parts
                return relative_parts
            else:
                # 非标准Windows路径（如UNC路径）
                return list(path_parts)
        else:
            # Linux/macOS: 绝对路径从 '/' 开始
            if path_parts[0] == '/':
                # 跳过根目录，保留从第一个目录开始的结构
                if len(path_parts) > 1:
                    return list(path_parts[1:])
                else:
                    return ['root']
            else:
                # 相对路径，直接使用
                return list(path_parts)
    
    def _is_windows_drive(self, path_part: str) -> bool:
        """
        检查路径部分是否是Windows驱动器号（跨平台兼容）
        
        Args:
            path_part: 路径部分（如 'F:\\' 或 'F:'）
            
        Returns:
            是否是Windows驱动器号
        """
        if self._platform != 'windows':
            return False
        
        # Windows驱动器格式: 'C:', 'C:\\', 'D:', 'D:\\' 等
        return (len(path_part) == 2 and path_part[1] == ':') or \
               (len(path_part) == 3 and path_part[1] == ':' and path_part[2] == '\\')
    
    def resolve_file_conflict(self, target_path: Path) -> Path:
        """
        解决文件冲突（如果目标文件已存在，添加序号）
        
        Args:
            target_path: 目标路径
            
        Returns:
            解决冲突后的路径
        """
        if not target_path.exists():
            return target_path
        
        counter = 1
        base_path = target_path
        while target_path.exists():
            stem = base_path.stem
            suffix = base_path.suffix
            target_path = base_path.parent / f"{stem}_{counter}{suffix}"
            counter += 1
        
        self._logger.debug(f"[回收站] 文件冲突已解决，新路径: {target_path}")
        return target_path
    
    def move_to_trash(self, source_path: Path, original_location: Optional[str] = None) -> Tuple[Path, str]:
        """
        移动文件到回收站
        
        Args:
            source_path: 源文件路径
            original_location: 原始位置（用于恢复），如果为None则使用source_path
            
        Returns:
            (回收站中的文件路径, 原始位置)
            
        Raises:
            FileNotFoundError: 源文件不存在
            PermissionError: 文件被占用或权限不足
            Exception: 其他错误
        """
        source_path = source_path.resolve()
        
        if not source_path.exists():
            raise FileNotFoundError(f"源文件不存在: {source_path}")
        
        # 记录原始位置
        if original_location is None:
            original_location = str(source_path.absolute())
        
        # 计算回收站路径
        trash_path = self.calculate_trash_path(source_path)
        
        # 确保目标目录存在（跨平台）
        self._ensure_directory_exists(trash_path.parent)
        
        # 解决文件冲突
        trash_path = self.resolve_file_conflict(trash_path)
        trash_path = trash_path.resolve()
        
        self._logger.info(f"[回收站] 准备移动文件: {source_path} -> {trash_path}")
        self._logger.debug(f"[回收站] 源文件存在: {source_path.exists()}, 目标目录存在: {trash_path.parent.exists()}")
        
        try:
            # 移动文件（跨平台兼容）
            self._move_file_cross_platform(source_path, trash_path)
            
            # 等待文件系统更新（Windows可能需要）
            time.sleep(0.1)
            
            # 验证文件已移动
            self._verify_move(source_path, trash_path)
            
            self._logger.info(f"[回收站] 文件已成功移动到回收站: {source_path} -> {trash_path}")
            return trash_path, original_location
            
        except PermissionError as e:
            self._logger.error(f"[回收站] 移动文件失败（权限错误）: {source_path}, 错误: {e}", exc_info=True)
            raise Exception(f"无法删除文件，文件可能正在被其他程序使用: {str(e)}")
        except FileNotFoundError as e:
            self._logger.error(f"[回收站] 移动文件失败（文件不存在）: {source_path}, 错误: {e}", exc_info=True)
            raise
        except Exception as e:
            self._logger.error(f"[回收站] 移动文件失败: {source_path}, 错误: {e}", exc_info=True)
            raise Exception(f"删除文件失败: {str(e)}")
    
    def _verify_move(self, source_path: Path, target_path: Path) -> None:
        """
        验证文件移动是否成功
        
        Args:
            source_path: 源文件路径
            target_path: 目标文件路径
            
        Raises:
            Exception: 如果移动验证失败
        """
        source_abs = source_path.resolve() if source_path.exists() else None
        target_abs = target_path.resolve()
        
        if not target_abs.exists():
            raise Exception(f"文件移动后不存在于目标位置: {target_abs}")
        
        if source_abs and source_abs.exists():
            # 再次等待并检查（可能是缓存问题）
            time.sleep(0.2)
            if source_abs.exists():
                self._logger.error(f"[回收站] 文件移动后仍存在于原位置: {source_abs}")
                raise Exception(f"文件移动后仍存在于原位置: {source_abs}")
    
    def restore_from_trash(self, current_path: Path, original_path: Path) -> Path:
        """
        从回收站恢复文件到原始位置
        
        Args:
            current_path: 文件当前路径（回收站中的路径）
            original_path: 原始路径（恢复目标）
            
        Returns:
            恢复后的文件路径（可能因为冲突而重命名）
            
        Raises:
            FileNotFoundError: 文件不存在
            PermissionError: 权限不足
            Exception: 其他错误
        """
        current_path = current_path.resolve()
        original_path = original_path.resolve()
        
        if not current_path.exists():
            raise FileNotFoundError(f"回收站中的文件不存在: {current_path}")
        
        # 确保原路径的目录存在（跨平台）
        self._ensure_directory_exists(original_path.parent)
        
        # 解决文件冲突
        restored_path = self.resolve_file_conflict(original_path)
        
        self._logger.info(f"[回收站] 准备恢复文件: {current_path} -> {restored_path}")
        
        try:
            # 移动文件回原路径（跨平台兼容）
            self._move_file_cross_platform(current_path, restored_path)
            
            # 等待文件系统更新
            time.sleep(0.1)
            
            # 验证文件已恢复
            if not restored_path.exists():
                raise Exception(f"文件恢复后不存在于目标位置: {restored_path}")
            
            self._logger.info(f"[回收站] 文件已成功恢复: {current_path} -> {restored_path}")
            return restored_path
            
        except PermissionError as e:
            self._logger.error(f"[回收站] 恢复文件失败（权限错误）: {current_path}, 错误: {e}", exc_info=True)
            raise Exception(f"无法恢复文件，可能权限不足: {str(e)}")
        except FileNotFoundError as e:
            self._logger.error(f"[回收站] 恢复文件失败（文件不存在）: {current_path}, 错误: {e}", exc_info=True)
            raise
        except Exception as e:
            self._logger.error(f"[回收站] 恢复文件失败: {current_path}, 错误: {e}", exc_info=True)
            raise Exception(f"恢复文件失败: {str(e)}")
    
    def _ensure_directory_exists(self, directory: Path) -> None:
        """
        确保目录存在（跨平台兼容）
        
        Args:
            directory: 目录路径
            
        Raises:
            OSError: 如果无法创建目录
        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            # 验证目录权限（Linux/macOS）
            if self._platform != 'windows':
                if not os.access(directory, os.W_OK):
                    raise PermissionError(f"目录无写权限: {directory}")
        except PermissionError:
            self._logger.error(f"[回收站] 无法创建目录（权限不足）: {directory}", exc_info=True)
            raise
        except Exception as e:
            self._logger.error(f"[回收站] 创建目录失败: {directory}, 错误: {e}", exc_info=True)
            raise
    
    def _move_file_cross_platform(self, source: Path, target: Path) -> None:
        """
        跨平台文件移动
        
        Args:
            source: 源文件路径
            target: 目标文件路径
            
        Raises:
            OSError: 如果移动失败
        """
        try:
            # 使用 pathlib 的字符串表示确保跨平台兼容
            source_str = str(source)
            target_str = str(target)
            
            # 在 Linux/macOS 上，确保目标目录有写权限
            if self._platform != 'windows':
                target_parent = target.parent
                if target_parent.exists() and not os.access(target_parent, os.W_OK):
                    raise PermissionError(f"目标目录无写权限: {target_parent}")
            
            # 执行移动操作
            move(source_str, target_str)
            
        except PermissionError as e:
            self._logger.error(f"[回收站] 文件移动失败（权限错误）: {source} -> {target}, 错误: {e}", exc_info=True)
            raise
        except OSError as e:
            self._logger.error(f"[回收站] 文件移动失败（系统错误）: {source} -> {target}, 错误: {e}", exc_info=True)
            raise
        except Exception as e:
            self._logger.error(f"[回收站] 文件移动失败（未知错误）: {source} -> {target}, 错误: {e}", exc_info=True)
            raise
"""ExifTool管理器 - 自动检测和使用项目内的ExifTool"""
import os
import platform
import subprocess
import urllib.request
import zipfile
import tarfile
import shutil
import time
from pathlib import Path
from typing import Optional


class ExifToolManager:
    """ExifTool管理器 - 自动检测系统PATH或项目内的ExifTool"""
    
    def __init__(self):
        """初始化ExifTool管理器"""
        self.project_root = Path(__file__).parent.parent
        self.exiftool_dir = self.project_root / "exiftool"
        self._exiftool_path = None
        self._detect_exiftool()
    
    def _detect_exiftool(self):
        """检测ExifTool路径（优先使用项目内的）"""
        # 1. 优先检查项目内的ExifTool
        project_exiftool = self._find_project_exiftool()
        if project_exiftool:
            self._exiftool_path = project_exiftool
            return
        
        # 2. 检查系统PATH中的ExifTool
        system_exiftool = self._find_system_exiftool()
        if system_exiftool:
            self._exiftool_path = system_exiftool
            return
        
        # 3. 未找到
        self._exiftool_path = None
    
    def _find_project_exiftool(self) -> Optional[Path]:
        """查找项目内的ExifTool"""
        system = platform.system().lower()
        
        # 如果目录中有压缩包但没有可执行文件，尝试解压
        if not self._has_executable():
            try:
                self._extract_archives()
            except Exception as e:
                # 解压失败不影响继续查找（可能文件正在使用）
                try:
                    print(f"解压失败（可能文件正在使用）: {e}")
                except UnicodeEncodeError:
                    print(f"Extraction failed (file may be in use): {e}")
        
        # 如果有可执行文件但缺少依赖文件（如exiftool_files目录），尝试重新解压
        if self._has_executable() and self._is_incomplete():
            # 尝试重新解压（如果有压缩包）
            try:
                self._extract_archives()
            except Exception as e:
                # 解压失败不影响继续查找（可能文件正在使用）
                try:
                    print(f"重新解压失败（可能文件正在使用）: {e}")
                except UnicodeEncodeError:
                    print(f"Re-extraction failed (file may be in use): {e}")
        
        # 清理可能存在的压缩文件（如果可执行文件已存在且完整）
        self._cleanup_archives()
        
        if system == 'windows':
            # Windows: exiftool.exe 或 exiftool(-k).exe
            exe_names = ['exiftool.exe', 'exiftool(-k).exe']
            for exe_name in exe_names:
                exe_path = self.exiftool_dir / exe_name
                if exe_path.exists() and exe_path.is_file():
                    return exe_path
        else:
            # macOS/Linux: exiftool 可执行文件
            exiftool_path = self.exiftool_dir / "exiftool"
            if exiftool_path.exists() and os.access(exiftool_path, os.X_OK):
                return exiftool_path
        
        return None
    
    def _is_incomplete(self) -> bool:
        """检查ExifTool安装是否完整（Windows需要exiftool_files目录）"""
        if not self.exiftool_dir.exists():
            return True
        
        system = platform.system().lower()
        if system == 'windows':
            # Windows版本需要exiftool_files目录
            exiftool_files_dir = self.exiftool_dir / "exiftool_files"
            if not exiftool_files_dir.exists() or not exiftool_files_dir.is_dir():
                return True  # 缺少依赖目录
            # 检查是否有DLL文件
            dll_files = list(exiftool_files_dir.glob("*.dll"))
            if not dll_files:
                return True  # 缺少DLL文件
        # Unix系统通常不需要额外目录
        
        return False
    
    def _has_executable(self) -> bool:
        """检查目录中是否有可执行文件"""
        if not self.exiftool_dir.exists():
            return False
        
        system = platform.system().lower()
        for item in self.exiftool_dir.iterdir():
            if item.is_file():
                name_lower = item.name.lower()
                if system == 'windows':
                    if name_lower.endswith('.exe'):
                        return True
                else:
                    if name_lower == 'exiftool' and os.access(item, os.X_OK):
                        return True
        return False
    
    def _extract_archives(self):
        """自动解压目录中的压缩包"""
        if not self.exiftool_dir.exists():
            return
        
        system = platform.system().lower()
        
        # 查找压缩包
        archives = []
        for item in self.exiftool_dir.iterdir():
            if item.is_file() and item.name != '.gitkeep':
                name_lower = item.name.lower()
                if name_lower.endswith('.zip'):
                    archives.append(('zip', item))
                elif name_lower.endswith(('.tar.gz', '.tgz')):
                    archives.append(('tar', item))
        
        if not archives:
            return
        
        try:
            print(f"发现 {len(archives)} 个压缩包，正在解压...")
        except UnicodeEncodeError:
            print(f"Found {len(archives)} archive(s), extracting...")
        
        for archive_type, archive_path in archives:
            try:
                if archive_type == 'zip' and system == 'windows':
                    self._extract_zip(archive_path)
                elif archive_type == 'tar' and system != 'windows':
                    self._extract_tar(archive_path)
            except PermissionError as e:
                # 文件被占用，提示用户但继续运行
                try:
                    print(f"解压 {archive_path.name} 失败: 文件正在使用中，请关闭相关程序后重试")
                except UnicodeEncodeError:
                    print(f"Extract {archive_path.name} failed: file is in use, please close related programs and retry")
            except PermissionError as e:
                # 文件被占用，提示用户但继续运行
                try:
                    print(f"解压 {archive_path.name} 失败: 文件正在使用中，请关闭相关程序后重试")
                except UnicodeEncodeError:
                    print(f"Extract {archive_path.name} failed: file is in use, please close related programs and retry")
            except Exception as e:
                try:
                    print(f"解压 {archive_path.name} 失败: {e}")
                except UnicodeEncodeError:
                    print(f"Extract {archive_path.name} failed: {e}")
    
    def _extract_zip(self, zip_path: Path):
        """解压ZIP文件（提取所有文件，保留目录结构）"""
        try:
            print(f"正在解压 {zip_path.name}...")
        except UnicodeEncodeError:
            print(f"Extracting {zip_path.name}...")
        
        # 解压整个ZIP文件到临时目录
        temp_dir = self.exiftool_dir / "temp_extract"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 查找exiftool(-k).exe或exiftool.exe
            exe_found = None
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower() in ['exiftool(-k).exe', 'exiftool.exe']:
                        exe_found = Path(root) / file
                        break
                if exe_found:
                    break
            
            if exe_found:
                # 将整个解压目录的内容移动到exiftool目录（保留目录结构）
                # 找到解压后的根目录（通常是第一个子目录）
                extracted_root = None
                for item in temp_dir.iterdir():
                    if item.is_dir():
                        extracted_root = item
                        break
                
                if extracted_root:
                    # 移动整个目录结构（包括所有文件和子目录，使用rglob递归）
                    for item in extracted_root.rglob('*'):
                        if item.is_file():
                            # 计算相对路径
                            rel_path = item.relative_to(extracted_root)
                            target = self.exiftool_dir / rel_path
                            # 创建目标目录
                            target.parent.mkdir(parents=True, exist_ok=True)
                            # 移动文件（处理文件被占用的情况）
                            if target.exists():
                                self._safe_remove_file(target)
                            shutil.move(str(item), str(target))
                else:
                    # 如果没有子目录，直接移动文件
                    for item in temp_dir.iterdir():
                        if item.name != temp_dir.name:
                            target = self.exiftool_dir / item.name
                            if target.exists():
                                if target.is_file():
                                    self._safe_remove_file(target)
                                else:
                                    shutil.rmtree(target)
                            shutil.move(str(item), str(target))
            
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            # 查找最终的可执行文件
            exe_name = "exiftool(-k).exe"
            target_exe = self.exiftool_dir / exe_name
            if not target_exe.exists():
                target_exe = self.exiftool_dir / "exiftool.exe"
            
            if target_exe.exists():
                try:
                    print(f"已解压: {target_exe.name}")
                except UnicodeEncodeError:
                    print(f"Extracted: {target_exe.name}")
        except Exception as e:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
    
    def _extract_tar(self, tar_path: Path):
        """解压TAR.GZ文件"""
        target_exe = self.exiftool_dir / "exiftool"
        
        try:
            print(f"正在解压 {tar_path.name}...")
        except UnicodeEncodeError:
            print(f"Extracting {tar_path.name}...")
        
        with tarfile.open(tar_path, 'r:gz') as tar_ref:
            # 查找exiftool文件
            for member in tar_ref.getmembers():
                if member.name.endswith('/exiftool') and member.isfile():
                    member.name = 'exiftool'
                    tar_ref.extract(member, self.exiftool_dir)
                    break
            
            # 如果没找到，提取整个目录
            if not target_exe.exists():
                tar_ref.extractall(self.exiftool_dir)
                for extracted_file in self.exiftool_dir.rglob('exiftool'):
                    if extracted_file.is_file() and extracted_file != target_exe:
                        shutil.move(str(extracted_file), str(target_exe))
                        break
        
        # 设置执行权限
        if target_exe.exists():
            os.chmod(target_exe, 0o755)
            try:
                print(f"已解压: {target_exe.name}")
            except UnicodeEncodeError:
                print(f"Extracted: {target_exe.name}")
    
    def _safe_remove_file(self, file_path: Path, max_retries: int = 3):
        """
        安全删除文件，处理文件被占用的情况
        
        Args:
            file_path: 要删除的文件路径
            max_retries: 最大重试次数
        """
        if not file_path.exists():
            return
        
        for attempt in range(max_retries):
            try:
                # 尝试直接删除
                file_path.unlink()
                return
            except PermissionError:
                if attempt < max_retries - 1:
                    # 文件可能正在使用，等待后重试
                    time.sleep(0.5)
                else:
                    # 最后一次尝试：重命名文件而不是删除
                    try:
                        backup_name = f"{file_path.name}.old_{int(time.time())}"
                        backup_path = file_path.parent / backup_name
                        file_path.rename(backup_path)
                        # 稍后清理旧文件（非阻塞）
                        try:
                            # 延迟删除，避免立即失败
                            time.sleep(0.1)
                            if backup_path.exists():
                                backup_path.unlink()
                        except:
                            pass
                    except Exception:
                        # 如果重命名也失败，跳过这个文件
                        try:
                            print(f"警告: 无法替换 {file_path.name}，文件可能正在使用中")
                        except UnicodeEncodeError:
                            print(f"Warning: Cannot replace {file_path.name}, file may be in use")
            except Exception as e:
                # 其他错误，直接抛出
                raise
    
    def _cleanup_archives(self):
        """清理临时解压文件（保留压缩包）"""
        if not self.exiftool_dir.exists():
            return
        
        # 只清理临时解压目录，不删除压缩包
        # 压缩包保留在目录中，用户可以重复使用
        temp_dirs = ['temp_extract']
        for temp_dir_name in temp_dirs:
            temp_dir = self.exiftool_dir / temp_dir_name
            if temp_dir.exists() and temp_dir.is_dir():
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
    
    def _find_system_exiftool(self) -> Optional[str]:
        """查找系统PATH中的ExifTool"""
        try:
            result = subprocess.run(
                ['exiftool', '-ver'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return 'exiftool'
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None
    
    def get_exiftool_path(self) -> Optional[str]:
        """获取ExifTool路径"""
        if self._exiftool_path:
            return str(self._exiftool_path)
        return None
    
    def is_available(self) -> bool:
        """检查ExifTool是否可用"""
        if not self._exiftool_path:
            return False
        
        try:
            exe_path = Path(self._exiftool_path)
            if not exe_path.exists():
                return False
            
            # 设置工作目录为exiftool目录，这样exiftool(-k).exe能找到依赖的DLL文件
            # 使用 stdin=subprocess.DEVNULL 避免等待用户输入（处理 "press ENTER" 提示）
            result = subprocess.run(
                [str(exe_path.absolute()), '-ver'],
                capture_output=True,
                text=True,
                timeout=10,  # 增加超时时间
                cwd=str(self.exiftool_dir),  # 设置工作目录为exiftool目录
                stdin=subprocess.DEVNULL,  # 避免等待输入
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0  # Windows下不显示窗口
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False
        except Exception:
            # 捕获其他异常（如权限问题等），但不影响可用性检查
            return False
    
    def extract_exiftool(self) -> bool:
        """
        自动解压目录中的ExifTool压缩包
        
        Returns:
            是否成功解压
        """
        if self.is_available():
            return True  # 已经可用，无需解压
        
        if not self.exiftool_dir.exists():
            return False
        
        # 解压压缩包
        self._extract_archives()
        
        # 解压后重新检测ExifTool路径
        # 注意：_find_project_exiftool 内部会调用 _extract_archives 和 _detect_exiftool
        # 但为了确保检测到新解压的文件，我们显式调用 _detect_exiftool
        self._detect_exiftool()
        
        # 再次检查可用性（可能需要等待文件系统更新）
        # 如果仍然不可用，尝试再次检测
        if not self.is_available():
            # 等待一小段时间，确保文件系统已更新
            import time
            time.sleep(0.1)
            # 再次检测
            self._detect_exiftool()
        
        return self.is_available()
    
    def download_exiftool(self, auto: bool = False) -> bool:
        """
        自动下载ExifTool到项目目录
        
        Args:
            auto: 是否自动下载（不询问用户）
            
        Returns:
            是否成功下载
        """
        if self.is_available():
            return True  # 已经可用，无需下载
        
        system = platform.system().lower()
        self.exiftool_dir.mkdir(exist_ok=True)
        
        try:
            if system == 'windows':
                return self._download_windows()
            else:
                return self._download_unix()
        except Exception as e:
            print(f"下载ExifTool失败: {e}")
            return False
    
    def _download_windows(self) -> bool:
        """下载Windows版本的ExifTool"""
        print("正在下载ExifTool (Windows)...")
        
        url = "https://exiftool.org/exiftool-12.80.zip"
        zip_path = self.exiftool_dir / "exiftool.zip"
        exe_name = "exiftool(-k).exe"
        target_exe = self.exiftool_dir / exe_name
        
        try:
            # 下载文件
            print(f"从 {url} 下载...")
            urllib.request.urlretrieve(url, zip_path)
            print("下载完成，正在解压...")
            
            # 解压ZIP文件
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 查找exiftool(-k).exe文件
                found = False
                for file_info in zip_ref.namelist():
                    # 查找exiftool(-k).exe或exiftool.exe
                    if file_info.endswith('exiftool(-k).exe') or file_info.endswith('exiftool.exe'):
                        # 提取文件
                        zip_ref.extract(file_info, self.exiftool_dir)
                        # 如果文件在子目录中，移动到exiftool目录
                        extracted_path = self.exiftool_dir / file_info
                        if extracted_path.exists():
                            # 如果不在目标位置，移动到目标位置
                            if extracted_path != target_exe:
                                # 如果目标文件已存在，先删除
                                if target_exe.exists():
                                    target_exe.unlink()
                                # 移动文件
                                shutil.move(str(extracted_path), str(target_exe))
                            found = True
                            break
                
                # 如果没找到exiftool(-k).exe，尝试找exiftool.exe
                if not found:
                    for file_info in zip_ref.namelist():
                        if file_info.endswith('exiftool.exe'):
                            zip_ref.extract(file_info, self.exiftool_dir)
                            extracted_path = self.exiftool_dir / file_info
                            if extracted_path.exists() and extracted_path != target_exe:
                                if target_exe.exists():
                                    target_exe.unlink()
                                shutil.move(str(extracted_path), str(target_exe))
                                found = True
                                break
                
                # 清理可能创建的子目录
                for item in self.exiftool_dir.iterdir():
                    if item.is_dir() and item.name != '.gitkeep':
                        try:
                            # 检查目录是否为空
                            if not any(item.iterdir()):
                                item.rmdir()
                        except:
                            pass
            
            # 保留ZIP文件，不删除（用户可以重复使用）
            
            # 验证文件是否存在
            if target_exe.exists():
                print(f"✓ ExifTool已下载到: {target_exe}")
                # 重新检测
                self._detect_exiftool()
                return self.is_available()
            else:
                print("✗ 解压失败：未找到exiftool(-k).exe")
                return False
                
        except Exception as e:
            print(f"✗ 下载失败: {e}")
            if zip_path.exists():
                zip_path.unlink()
            return False
    
    def _download_unix(self) -> bool:
        """下载Unix版本（macOS/Linux）的ExifTool"""
        print("正在下载ExifTool (macOS/Linux)...")
        
        url = "https://exiftool.org/Image-ExifTool-12.80.tar.gz"
        tar_path = self.exiftool_dir / "Image-ExifTool.tar.gz"
        target_exe = self.exiftool_dir / "exiftool"
        
        try:
            # 下载文件
            print(f"从 {url} 下载...")
            urllib.request.urlretrieve(url, tar_path)
            print("下载完成，正在解压...")
            
            # 解压TAR.GZ文件
            with tarfile.open(tar_path, 'r:gz') as tar_ref:
                # 查找exiftool文件
                for member in tar_ref.getmembers():
                    if member.name.endswith('/exiftool') and member.isfile():
                        # 提取文件
                        member.name = 'exiftool'  # 重命名为exiftool
                        tar_ref.extract(member, self.exiftool_dir)
                        break
                
                # 如果没找到，尝试提取整个目录
                if not target_exe.exists():
                    tar_ref.extractall(self.exiftool_dir)
                    # 查找exiftool文件
                    for extracted_file in self.exiftool_dir.rglob('exiftool'):
                        if extracted_file.is_file() and extracted_file != target_exe:
                            shutil.move(str(extracted_file), str(target_exe))
                            # 删除空目录
                            try:
                                extracted_file.parent.rmdir()
                            except:
                                pass
                            break
            
            # 保留TAR文件，不删除（用户可以重复使用）
            
            # 设置执行权限
            if target_exe.exists():
                os.chmod(target_exe, 0o755)
                print(f"✓ ExifTool已下载到: {target_exe}")
                # 重新检测
                self._detect_exiftool()
                return self.is_available()
            else:
                print("✗ 解压失败：未找到exiftool文件")
                return False
                
        except Exception as e:
            print(f"✗ 下载失败: {e}")
            if tar_path.exists():
                tar_path.unlink()
            return False
    
    def get_download_info(self) -> dict:
        """获取ExifTool下载信息"""
        system = platform.system().lower()
        
        if system == 'windows':
            return {
                'platform': 'Windows',
                'url': 'https://exiftool.org/exiftool-12.80.zip',
                'filename': 'exiftool-12.80.zip',
                'extract_to': str(self.exiftool_dir),
                'executable': 'exiftool(-k).exe',
                'instructions': [
                    '1. 下载 exiftool-12.80.zip',
                    '2. 解压到项目根目录下的 exiftool/ 文件夹',
                    '3. 确保 exiftool(-k).exe 文件在 exiftool/ 目录中'
                ]
            }
        elif system == 'darwin':  # macOS
            return {
                'platform': 'macOS',
                'url': 'https://exiftool.org/Image-ExifTool-12.80.tar.gz',
                'filename': 'Image-ExifTool-12.80.tar.gz',
                'extract_to': str(self.exiftool_dir),
                'executable': 'exiftool',
                'instructions': [
                    '1. 下载 Image-ExifTool-12.80.tar.gz',
                    '2. 解压到项目根目录下的 exiftool/ 文件夹',
                    '3. 确保 exiftool 文件在 exiftool/ 目录中',
                    '4. 运行: chmod +x exiftool/exiftool'
                ]
            }
        else:  # Linux
            return {
                'platform': 'Linux',
                'url': 'https://exiftool.org/Image-ExifTool-12.80.tar.gz',
                'filename': 'Image-ExifTool-12.80.tar.gz',
                'extract_to': str(self.exiftool_dir),
                'executable': 'exiftool',
                'instructions': [
                    '1. 下载 Image-ExifTool-12.80.tar.gz',
                    '2. 解压到项目根目录下的 exiftool/ 文件夹',
                    '3. 确保 exiftool 文件在 exiftool/ 目录中',
                    '4. 运行: chmod +x exiftool/exiftool'
                ]
            }

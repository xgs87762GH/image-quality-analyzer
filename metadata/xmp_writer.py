"""XMP元数据写入器"""
import json
import subprocess
from typing import Dict, Optional
from utils.constants import XMP_FIELDS


class XMPWriter:
    """XMP元数据写入器 - 使用exiftool"""
    
    def __init__(self, exiftool_path: str = "exiftool"):
        """
        初始化XMP写入器
        
        Args:
            exiftool_path: exiftool可执行文件路径
        """
        self.exiftool_path = exiftool_path
        self._available = self._check_exiftool()
    
    def _check_exiftool(self) -> bool:
        """检查exiftool是否可用"""
        try:
            result = subprocess.run(
                [self.exiftool_path, "-ver"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"exiftool 版本: {result.stdout.strip()}")
                return True
            return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("警告: 未找到exiftool，将无法写入元数据")
            print("请安装exiftool:")
            print("  Windows: 下载 https://exiftool.org/")
            print("  macOS: brew install exiftool")
            print("  Ubuntu: sudo apt-get install libimage-exiftool-perl")
            return False
    
    def is_available(self) -> bool:
        """检查exiftool是否可用"""
        return self._available
    
    def write(self, image_path: str, analysis_result: Dict, 
              backup: bool = True) -> bool:
        """
        将分析结果写入图像XMP元数据
        
        Args:
            image_path: 图像文件路径
            analysis_result: 分析结果字典
            backup: 是否创建备份
            
        Returns:
            是否成功写入
        """
        if not self._available or not analysis_result:
            return False
        
        try:
            cmd = [self.exiftool_path]
            
            if backup:
                cmd.append("-overwrite_original")
            else:
                cmd.append("-overwrite_original_in_place")
            
            fields = XMP_FIELDS
            
            # XMP Rating (1-5)
            cmd.extend([f"-{fields['rating']}", str(analysis_result["rating"])])
            
            # XMP Label
            cmd.extend([f"-{fields['label']}", analysis_result["label"]])
            
            # XMP Subject (关键词列表，用分号分隔)
            subjects_str = ";".join(analysis_result["subjects"])
            cmd.extend([f"-{fields['subject']}", subjects_str])
            
            # XMP Description (存储详细JSON)
            description = json.dumps(analysis_result["metrics"], ensure_ascii=False)
            if len(description) > 500:
                description = description[:500] + "..."
            cmd.extend([f"-{fields['description']}", f"QualityAnalysis: {description}"])
            
            # 添加文件路径
            cmd.append(str(image_path))
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.returncode == 0
        except Exception as e:
            print(f"写入元数据时出错: {e}")
            return False

"""XMP元数据读取器"""
import json
import subprocess
from typing import Dict, List
from pathlib import Path
from utils.constants import XMP_FIELDS, DEFAULT_IMAGE_EXTENSIONS


class XMPReader:
    """XMP元数据读取器 - 使用exiftool"""
    
    def __init__(self, exiftool_path: str = "exiftool"):
        """
        初始化XMP读取器
        
        Args:
            exiftool_path: exiftool可执行文件路径
        """
        self.exiftool_path = exiftool_path
        self._check_exiftool()
    
    def _check_exiftool(self):
        """检查exiftool是否可用"""
        try:
            result = subprocess.run(
                [self.exiftool_path, "-ver"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise FileNotFoundError("exiftool未正确安装")
        except FileNotFoundError:
            print("错误: 未找到exiftool")
            raise
    
    def read(self, image_path: str) -> Dict:
        """
        读取图像的XMP元数据
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            元数据字典
        """
        try:
            fields = XMP_FIELDS
            cmd = [
                self.exiftool_path,
                "-j",  # JSON输出
                f"-{fields['rating']}",
                f"-{fields['label']}",
                f"-{fields['subject']}",
                f"-{fields['description']}",
                str(image_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                if data and len(data) > 0:
                    return data[0]
            return {}
        except Exception as e:
            print(f"读取元数据失败 {image_path}: {e}")
            return {}
    
    def find_by_rating(self, directory: str, max_rating: int = 2) -> List[str]:
        """查找评级低于等于指定值的图像"""
        images = []
        for img_path in Path(directory).rglob("*"):
            if img_path.suffix.lower() in DEFAULT_IMAGE_EXTENSIONS:
                metadata = self.read(str(img_path))
                rating = metadata.get("Rating", None)
                if rating is not None:
                    try:
                        if int(rating) <= max_rating:
                            images.append(str(img_path))
                    except (ValueError, TypeError):
                        pass
        return images
    
    def find_by_label(self, directory: str, labels: List[str]) -> List[str]:
        """查找指定标签的图像"""
        images = []
        labels_lower = [l.lower() for l in labels]
        for img_path in Path(directory).rglob("*"):
            if img_path.suffix.lower() in DEFAULT_IMAGE_EXTENSIONS:
                metadata = self.read(str(img_path))
                label = metadata.get("Label", "")
                if label and label.lower() in labels_lower:
                    images.append(str(img_path))
        return images
    
    def find_by_subject(self, directory: str, keywords: List[str]) -> List[str]:
        """查找包含指定关键词的图像"""
        images = []
        keywords_lower = [k.lower() for k in keywords]
        for img_path in Path(directory).rglob("*"):
            if img_path.suffix.lower() in DEFAULT_IMAGE_EXTENSIONS:
                metadata = self.read(str(img_path))
                subjects = metadata.get("Subject", "")
                if isinstance(subjects, str):
                    subjects_list = [s.strip().lower() for s in subjects.split(";")]
                elif isinstance(subjects, list):
                    subjects_list = [s.lower() for s in subjects]
                else:
                    subjects_list = []
                
                if any(kw in subjects_list for kw in keywords_lower):
                    images.append(str(img_path))
        return images

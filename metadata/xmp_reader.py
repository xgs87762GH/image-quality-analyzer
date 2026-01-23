"""XMP元数据读取器"""
import json
from typing import Dict, List
from pathlib import Path
from utils.constants import XMP_FIELDS, DEFAULT_IMAGE_EXTENSIONS
from utils.exiftool_executor import ExifToolExecutor
from utils.logger import get_logger


class XMPReader:
    """XMP元数据读取器 - 使用exiftool"""
    
    def __init__(self):
        """初始化XMP读取器"""
        self._executor = ExifToolExecutor()
        self._logger = get_logger()
    
    def is_available(self) -> bool:
        """检查exiftool是否可用"""
        return self._executor.is_available()
    
    def read(self, image_path: str) -> Dict:
        """
        读取图像的XMP元数据
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            元数据字典
        """
        if not self.is_available():
            self._logger.warning(f"ExifTool不可用，无法读取XMP: {image_path}")
            return {}
        
        try:
            # 确保路径是有效的字符串（处理中文路径编码问题）
            if isinstance(image_path, Path):
                image_path_str = str(image_path.resolve())
            else:
                image_path_str = str(image_path)
                # 确保是有效的UTF-8
                try:
                    image_path_str.encode('utf-8').decode('utf-8')
                except (UnicodeEncodeError, UnicodeDecodeError):
                    image_path_str = image_path_str.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
            
            fields = XMP_FIELDS
            args = [
                "-j",  # JSON输出
                f"-{fields['rating']}",
                f"-{fields['label']}",
                f"-{fields['subject']}",
                f"-{fields['description']}",
                image_path_str
            ]
            
            result = self._executor.execute(args, timeout=10)
            
            if result['success'] and result['stdout']:
                data = json.loads(result['stdout'])
                if data and len(data) > 0:
                    self._logger.debug(f"成功读取XMP: {image_path}")
                    return data[0]
            
            return {}
        except Exception as e:
            self._logger.error(f"读取XMP失败: {image_path}, 错误: {e}")
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

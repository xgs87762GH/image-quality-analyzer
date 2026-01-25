"""图像质量分析器 - 计算基础质量指标（高内聚：质量指标计算逻辑集中）"""
from typing import Optional
import numpy as np
import cv2

from analyzers.base_analyzer import BaseAnalyzer


class QualityAnalyzer(BaseAnalyzer):
    """图像质量分析器 - 计算模糊度、亮度、信息熵等基础指标"""
    
    def analyze(self, image_path: str) -> Optional[dict]:
        """
        分析图像（实现BaseAnalyzer接口）
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            分析结果字典，包含基础质量指标
        """
        try:
            import numpy as np
            from PIL import Image
            
            img = Image.open(image_path)
            img_array = np.array(img.convert('RGB'))
            
            return {
                'blur_score': self.calculate_blur_score(img_array),
                'brightness': self.calculate_brightness(img_array),
                'entropy': self.calculate_entropy(img_array),
                'brisque': self.calculate_brisque(img_array)
            }
        except Exception:
            return None
    
    def is_available(self) -> bool:
        """检查分析器是否可用"""
        try:
            import cv2
            import numpy as np
            return True
        except ImportError:
            return False
    
    @staticmethod
    def calculate_blur_score(image: np.ndarray) -> float:
        """
        计算模糊度（Laplacian方差）
        
        Args:
            image: RGB图像数组
            
        Returns:
            模糊度分数，值越大越清晰
        """
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return float(laplacian_var)
    
    @staticmethod
    def calculate_brightness(image: np.ndarray) -> float:
        """
        计算平均亮度
        
        Args:
            image: RGB图像数组
            
        Returns:
            平均亮度值（0-255）
        """
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        return float(np.mean(gray))
    
    @staticmethod
    def calculate_entropy(image: np.ndarray) -> float:
        """
        计算信息熵
        
        Args:
            image: RGB图像数组
            
        Returns:
            信息熵值，值越大信息量越高
        """
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        hist, _ = np.histogram(gray.flatten(), bins=256, range=(0, 256))
        hist = hist[hist > 0]  # 去除零值
        prob = hist / hist.sum()
        entropy = -np.sum(prob * np.log2(prob))
        return float(entropy)
    
    @staticmethod
    def calculate_brisque(image: np.ndarray, 
                         model_path: str = "brisque_model.yml",
                         range_path: str = "brisque_range.yml") -> Optional[float]:
        """
        计算BRISQUE分数（无参考图像质量评估）
        
        Args:
            image: RGB图像数组
            model_path: BRISQUE模型文件路径
            range_path: BRISQUE范围文件路径
            
        Returns:
            BRISQUE分数（越低越好，通常0-100），如果不可用则返回None
        """
        try:
            if not hasattr(cv2, 'quality'):
                return None
            
            try:
                from cv2.quality import QualityBRISQUE
            except ImportError:
                return None
            
            # 检查模型文件是否存在（在尝试加载前检查，避免 OpenCV 输出错误信息）
            import os
            if not os.path.exists(model_path) or not os.path.exists(range_path):
                # BRISQUE 模型文件不存在，静默返回 None（这是可选功能）
                # 注意：BRISQUE 模型文件需要从 OpenCV 源码或官方资源下载
                # 下载地址：https://github.com/opencv/opencv_contrib/tree/master/modules/quality/samples
                return None
            
            # 临时抑制 OpenCV 的错误输出（cv2.error 会输出到 stderr）
            import sys
            from io import StringIO
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            
            # 同时设置 OpenCV 日志级别为 ERROR（减少输出）
            old_log_level = cv2.getLogLevel()
            cv2.setLogLevel(cv2.LOG_LEVEL_ERROR)
            
            try:
                # BRISQUE需要BGR格式
                bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) if len(image.shape) == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                
                detector = QualityBRISQUE.create(model_path, range_path)
                score = detector.compute(bgr)
                result = float(score[0])
                # 恢复设置
                sys.stderr = old_stderr
                cv2.setLogLevel(old_log_level)
                return result
            except (FileNotFoundError, cv2.error):
                # 恢复设置
                sys.stderr = old_stderr
                cv2.setLogLevel(old_log_level)
                return None
            except Exception:
                # 恢复设置
                sys.stderr = old_stderr
                cv2.setLogLevel(old_log_level)
                return None
        except Exception:
            return None

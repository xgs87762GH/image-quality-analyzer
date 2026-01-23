"""图像分析器 - 整合质量分析和审美评分（高内聚：图像分析流程整合）"""
from typing import Dict, Optional, Any
import numpy as np
from PIL import Image

from analyzers.base_analyzer import BaseAnalyzer
from analyzers.quality_analyzer import QualityAnalyzer
from analyzers.aesthetic_analyzer import AestheticAnalyzer
from analyzers.calculators.metric_normalizer import MetricNormalizer
from analyzers.calculators.quality_calculator import QualityCalculator


class ImageAnalyzer(BaseAnalyzer):
    """图像分析器 - 整合质量分析和审美评分"""
    
    def __init__(self, use_aesthetic: bool = False, aesthetic_mode: str = 'none', 
                 ai_analyzer: Optional[Any] = None):
        """
        初始化图像分析器
        
        Args:
            use_aesthetic: 是否启用审美评分（向后兼容，将被aesthetic_mode替代）
            aesthetic_mode: 审美评估方式 ('none', 'clip', 'ai')
            ai_analyzer: AI分析器实例（当aesthetic_mode='ai'时需要）
        """
        # 向后兼容：如果use_aesthetic为True但aesthetic_mode为'none'，则设置为'clip'
        if use_aesthetic and aesthetic_mode == 'none':
            aesthetic_mode = 'clip'
        
        self.aesthetic_mode = aesthetic_mode
        self.quality_analyzer = QualityAnalyzer()
        
        # 根据模式初始化相应的分析器
        if aesthetic_mode == 'clip':
            self.aesthetic_analyzer = AestheticAnalyzer()
            # 如果启用审美评分但模型不可用，则禁用
            if not self.aesthetic_analyzer.is_available():
                print("警告: CLIP审美评分模型不可用，将仅使用质量分析")
                self.aesthetic_mode = 'none'
                self.aesthetic_analyzer = None
        elif aesthetic_mode == 'ai':
            self.ai_analyzer = ai_analyzer
            self.aesthetic_analyzer = None
            if not self.ai_analyzer:
                print("警告: AI分析器未提供，将仅使用质量分析")
                self.aesthetic_mode = 'none'
        else:
            self.aesthetic_analyzer = None
            self.ai_analyzer = None
        
        # 向后兼容
        self.use_aesthetic = (self.aesthetic_mode != 'none')
    
    def is_available(self) -> bool:
        """检查分析器是否可用"""
        return self.quality_analyzer.is_available()
    
    def analyze(self, image_path: str) -> Optional[Dict]:
        """
        分析单张图像
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            分析结果字典，包含质量分数、评级、标签等，如果失败则返回None
        """
        try:
            # 读取图像
            img = Image.open(image_path)
            img_array = np.array(img.convert('RGB'))
            
            # 计算基础质量指标
            blur_score = self.quality_analyzer.calculate_blur_score(img_array)
            brightness = self.quality_analyzer.calculate_brightness(img_array)
            entropy = self.quality_analyzer.calculate_entropy(img_array)
            brisque = self.quality_analyzer.calculate_brisque(img_array)
            
            # 可选：审美评分（根据模式选择）
            aesthetic_score = None
            if self.aesthetic_mode == 'clip' and self.aesthetic_analyzer:
                aesthetic_score = self.aesthetic_analyzer.calculate_score(img_array)
            elif self.aesthetic_mode == 'ai' and self.ai_analyzer:
                aesthetic_score = self.ai_analyzer.calculate_aesthetic_score(image_path)
            
            # 归一化指标（使用计算器模块）
            blur_norm, brightness_norm, entropy_norm = MetricNormalizer.normalize_quality_metrics(
                blur_score, brightness, entropy
            )
            
            # 归一化审美评分
            aesthetic_norm = None
            if aesthetic_score is not None:
                aesthetic_norm = MetricNormalizer.normalize_aesthetic_score(aesthetic_score)
            
            # 计算综合质量分数（使用计算器模块）
            quality_score = QualityCalculator.calculate_quality_score(
                blur_norm, brightness_norm, entropy_norm, aesthetic_norm
            )
            
            # 获取评级和标签（使用计算器模块）
            rating = QualityCalculator.get_rating(quality_score)
            label = QualityCalculator.get_label(quality_score)
            subjects = QualityCalculator.get_subjects(blur_score, brightness, entropy, brisque, label)
            
            return {
                "quality_score": round(quality_score, 2),
                "rating": rating,
                "label": label,
                "subjects": subjects,
                "metrics": {
                    "blur_score": round(blur_score, 2),
                    "brightness": round(brightness, 2),
                    "entropy": round(entropy, 2),
                    "brisque": round(brisque, 2) if brisque else None,
                    "aesthetic_score": round(aesthetic_score, 2) if aesthetic_score else None
                }
            }
        except Exception as e:
            print(f"分析图像 {image_path} 时出错: {e}")
            return None

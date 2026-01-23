"""指标归一化器（高内聚：归一化逻辑集中）"""
from typing import Tuple, Optional
from utils.constants import NORMALIZATION_PARAMS


class MetricNormalizer:
    """指标归一化器 - 负责将原始指标归一化到0-100范围"""
    
    @staticmethod
    def normalize_quality_metrics(blur_score: float, brightness: float, 
                                  entropy: float) -> Tuple[float, float, float]:
        """
        归一化质量指标到0-100
        
        Args:
            blur_score: 模糊度分数
            brightness: 亮度值
            entropy: 信息熵
            
        Returns:
            (blur_norm, brightness_norm, entropy_norm)
        """
        params = NORMALIZATION_PARAMS
        
        # 模糊度归一化
        blur_norm = min(100, (blur_score / params['blur_threshold']) * 100)
        
        # 亮度归一化（理想值150）
        brightness_norm = 100 - abs(brightness - params['brightness_ideal']) / params['brightness_tolerance']
        brightness_norm = max(0, min(100, brightness_norm))
        
        # 熵归一化
        entropy_norm = min(100, (entropy / params['entropy_threshold']) * 100)
        
        return blur_norm, brightness_norm, entropy_norm
    
    @staticmethod
    def normalize_aesthetic_score(aesthetic_score: float) -> float:
        """
        归一化审美评分到0-100
        
        Args:
            aesthetic_score: 原始审美评分（0-10）
            
        Returns:
            归一化后的评分（0-100）
        """
        return (aesthetic_score / NORMALIZATION_PARAMS['aesthetic_max']) * 100

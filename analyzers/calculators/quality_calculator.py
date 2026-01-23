"""质量分数计算器（高内聚：质量计算逻辑集中）"""
from typing import Optional
from utils.constants import QUALITY_THRESHOLDS, QUALITY_LABELS, QUALITY_WEIGHTS, ISSUE_THRESHOLDS


class QualityCalculator:
    """质量分数计算器 - 负责计算综合质量分数、评级、标签等"""
    
    @staticmethod
    def calculate_quality_score(blur_norm: float, brightness_norm: float,
                               entropy_norm: float, aesthetic_norm: Optional[float] = None) -> float:
        """
        计算综合质量分数
        
        Args:
            blur_norm: 归一化模糊度
            brightness_norm: 归一化亮度
            entropy_norm: 归一化信息熵
            aesthetic_norm: 归一化审美评分（可选）
            
        Returns:
            综合质量分数（0-100）
        """
        weights = QUALITY_WEIGHTS
        
        # 基础质量分数
        quality_score = (
            blur_norm * weights['blur'] +
            brightness_norm * weights['brightness'] +
            entropy_norm * weights['entropy']
        )
        
        # 如果使用审美评分，加入权重
        if aesthetic_norm is not None:
            quality_score = quality_score * (1 - weights['aesthetic']) + aesthetic_norm * weights['aesthetic']
        
        return quality_score
    
    @staticmethod
    def get_rating(quality_score: float) -> int:
        """
        将质量分数映射到1-5星评级
        
        Args:
            quality_score: 质量分数（0-100）
            
        Returns:
            评级（1-5星）
        """
        return max(1, min(5, int((quality_score / 100) * 5) + 1))
    
    @staticmethod
    def get_label(quality_score: float) -> str:
        """
        根据质量分数获取标签
        
        Args:
            quality_score: 质量分数（0-100）
            
        Returns:
            标签字符串
        """
        thresholds = QUALITY_THRESHOLDS
        labels = QUALITY_LABELS
        
        if quality_score >= thresholds['HIGH']:
            return labels['HIGH']
        elif quality_score >= thresholds['MEDIUM']:
            return labels['MEDIUM']
        elif quality_score >= thresholds['LOW']:
            return labels['LOW']
        else:
            return labels['VERY_LOW']
    
    @staticmethod
    def get_subjects(blur_score: float, brightness: float, 
                    entropy: float, brisque: Optional[float], 
                    label: str) -> list:
        """
        生成Subject关键词列表
        
        Args:
            blur_score: 模糊度分数
            brightness: 亮度值
            entropy: 信息熵
            brisque: BRISQUE分数
            label: 质量标签
            
        Returns:
            关键词列表
        """
        subjects = [label.lower()]
        thresholds = ISSUE_THRESHOLDS
        
        if blur_score < thresholds['blur']:
            subjects.append("blurry")
        if brightness < thresholds['brightness_low'] or brightness > thresholds['brightness_high']:
            subjects.append("brightness_issue")
        if entropy < thresholds['entropy_low']:
            subjects.append("low_entropy")
        if brisque and brisque > thresholds['brisque_high']:
            subjects.append("high_distortion")
        
        return subjects

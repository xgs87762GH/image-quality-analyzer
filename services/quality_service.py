"""质量评估服务"""
from typing import List, Dict, Any, Optional

from database.connection import get_db
from repositories.quality_repository import QualityRepository
from repositories.image_repository import ImageRepository
from utils.logger import get_logger


class QualityService:
    """质量评估服务"""
    
    def __init__(self):
        """初始化质量评估服务"""
        self.db = get_db()
        self.quality_repo = QualityRepository(self.db)
        self.image_repo = ImageRepository(self.db)
        self.logger = get_logger()
    
    def find_by_rating(self, min_rating: int = 1, max_rating: int = 5) -> List[Dict[str, Any]]:
        """
        根据评级范围查找图像
        
        Args:
            min_rating: 最低评级
            max_rating: 最高评级
            
        Returns:
            图像信息列表
        """
        assessments = self.quality_repo.find_by_rating(min_rating, max_rating)
        results = []
        
        for assessment in assessments:
            image = self.image_repo.find_by_id(assessment.image_id)
            if image:
                results.append({
                    'image': image.to_dict(),
                    'quality': assessment.to_dict()
                })
        
        return results
    
    def find_by_label(self, label: str) -> List[Dict[str, Any]]:
        """
        根据标签查找图像
        
        Args:
            label: 质量标签
            
        Returns:
            图像信息列表
        """
        assessments = self.quality_repo.find_by_label(label)
        results = []
        
        for assessment in assessments:
            image = self.image_repo.find_by_id(assessment.image_id)
            if image:
                results.append({
                    'image': image.to_dict(),
                    'quality': assessment.to_dict()
                })
        
        return results
    
    def find_by_quality_range(self, min_score: float, max_score: float) -> List[Dict[str, Any]]:
        """
        根据质量分数范围查找图像
        
        Args:
            min_score: 最低分数
            max_score: 最高分数
            
        Returns:
            图像信息列表
        """
        assessments = self.quality_repo.find_by_quality_range(min_score, max_score)
        results = []
        
        for assessment in assessments:
            image = self.image_repo.find_by_id(assessment.image_id)
            if image:
                results.append({
                    'image': image.to_dict(),
                    'quality': assessment.to_dict()
                })
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取质量统计信息"""
        return self.quality_repo.get_statistics()

"""质量评估数据访问层"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from database.connection import DatabaseConnection
from database.models import QualityAssessment


class QualityRepository:
    """质量评估数据访问层"""
    
    def __init__(self, db: DatabaseConnection):
        """
        初始化质量评估仓库
        
        Args:
            db: 数据库连接
        """
        self.db = db
    
    def create_or_update(self, image_id: int, analysis_result: Dict[str, Any]) -> QualityAssessment:
        """
        创建或更新质量评估
        
        Args:
            image_id: 图像ID
            analysis_result: 分析结果字典
            
        Returns:
            质量评估对象
        """
        metrics = analysis_result.get('metrics', {})
        
        # 检查是否已存在
        existing = self.find_by_image_id(image_id)
        
        if existing:
            # 更新现有记录
            existing.quality_score = analysis_result.get('quality_score', 0.0)
            existing.rating = analysis_result.get('rating', 1)
            existing.label = analysis_result.get('label', '')
            existing.blur_score = metrics.get('blur_score')
            existing.brightness = metrics.get('brightness')
            existing.entropy = metrics.get('entropy')
            existing.brisque = metrics.get('brisque')
            existing.aesthetic_score = metrics.get('aesthetic_score')
            existing.updated_at = datetime.now()
            return self.update(existing)
        
        # 创建新记录
        assessment = QualityAssessment(
            image_id=image_id,
            quality_score=analysis_result.get('quality_score', 0.0),
            rating=analysis_result.get('rating', 1),
            label=analysis_result.get('label', ''),
            blur_score=metrics.get('blur_score'),
            brightness=metrics.get('brightness'),
            entropy=metrics.get('entropy'),
            brisque=metrics.get('brisque'),
            aesthetic_score=metrics.get('aesthetic_score')
        )
        
        with self.db.transaction() as conn:
            cursor = conn.execute(
                f"""
                INSERT INTO {QualityAssessment.TABLE_NAME}
                (image_id, quality_score, rating, label, blur_score, brightness, 
                 entropy, brisque, aesthetic_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assessment.image_id,
                    assessment.quality_score,
                    assessment.rating,
                    assessment.label,
                    assessment.blur_score,
                    assessment.brightness,
                    assessment.entropy,
                    assessment.brisque,
                    assessment.aesthetic_score
                )
            )
            assessment.id = cursor.lastrowid
        
        return assessment
    
    def find_by_id(self, assessment_id: int) -> Optional[QualityAssessment]:
        """根据ID查找质量评估"""
        cursor = self.db.execute(
            f"SELECT * FROM {QualityAssessment.TABLE_NAME} WHERE id = ?",
            (assessment_id,)
        )
        row = cursor.fetchone()
        return QualityAssessment.from_row(row) if row else None
    
    def find_by_image_id(self, image_id: int) -> Optional[QualityAssessment]:
        """根据图像ID查找质量评估"""
        cursor = self.db.execute(
            f"SELECT * FROM {QualityAssessment.TABLE_NAME} WHERE image_id = ?",
            (image_id,)
        )
        row = cursor.fetchone()
        return QualityAssessment.from_row(row) if row else None
    
    def update(self, assessment: QualityAssessment) -> QualityAssessment:
        """更新质量评估"""
        assessment.updated_at = datetime.now()
        
        with self.db.transaction() as conn:
            conn.execute(
                f"""
                UPDATE {QualityAssessment.TABLE_NAME}
                SET quality_score = ?, rating = ?, label = ?, blur_score = ?,
                    brightness = ?, entropy = ?, brisque = ?, aesthetic_score = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    assessment.quality_score,
                    assessment.rating,
                    assessment.label,
                    assessment.blur_score,
                    assessment.brightness,
                    assessment.entropy,
                    assessment.brisque,
                    assessment.aesthetic_score,
                    assessment.updated_at.isoformat(),
                    assessment.id
                )
            )
        
        return assessment
    
    def find_by_rating(self, min_rating: int = 1, max_rating: int = 5) -> List[QualityAssessment]:
        """根据评级范围查找"""
        cursor = self.db.execute(
            f"""
            SELECT * FROM {QualityAssessment.TABLE_NAME}
            WHERE rating >= ? AND rating <= ?
            ORDER BY rating DESC, quality_score DESC
            """,
            (min_rating, max_rating)
        )
        return [QualityAssessment.from_row(row) for row in cursor.fetchall()]
    
    def find_by_label(self, label: str) -> List[QualityAssessment]:
        """根据标签查找"""
        cursor = self.db.execute(
            f"""
            SELECT * FROM {QualityAssessment.TABLE_NAME}
            WHERE label = ?
            ORDER BY quality_score DESC
            """,
            (label,)
        )
        return [QualityAssessment.from_row(row) for row in cursor.fetchall()]
    
    def find_by_quality_range(self, min_score: float, max_score: float) -> List[QualityAssessment]:
        """根据质量分数范围查找"""
        cursor = self.db.execute(
            f"""
            SELECT * FROM {QualityAssessment.TABLE_NAME}
            WHERE quality_score >= ? AND quality_score <= ?
            ORDER BY quality_score DESC
            """,
            (min_score, max_score)
        )
        return [QualityAssessment.from_row(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        cursor = self.db.execute(
            f"""
            SELECT 
                COUNT(*) as total,
                AVG(quality_score) as avg_score,
                MIN(quality_score) as min_score,
                MAX(quality_score) as max_score,
                AVG(rating) as avg_rating
            FROM {QualityAssessment.TABLE_NAME}
            """
        )
        row = cursor.fetchone()
        return dict(row) if row else {}
    
    def delete_by_image_id(self, image_id: int) -> bool:
        """
        根据图像ID删除质量评估记录
        
        Args:
            image_id: 图像ID
            
        Returns:
            是否删除成功
        """
        with self.db.transaction() as conn:
            cursor = conn.execute(
                f"DELETE FROM {QualityAssessment.TABLE_NAME} WHERE image_id = ?",
                (image_id,)
            )
            return cursor.rowcount > 0
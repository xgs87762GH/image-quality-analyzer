"""元数据数据访问层"""
from datetime import datetime
from typing import Optional, List
import json

from database.connection import DatabaseConnection
from database.models import Metadata


class MetadataRepository:
    """元数据数据访问层"""
    
    def __init__(self, db: DatabaseConnection):
        """
        初始化元数据仓库
        
        Args:
            db: 数据库连接
        """
        self.db = db
    
    def create_or_update(self, image_id: int, xmp_data: dict) -> Metadata:
        """
        创建或更新元数据
        
        Args:
            image_id: 图像ID
            xmp_data: XMP数据字典（可包含 rating, label, subjects, description, ai_analysis, evaluations）
            
        Returns:
            元数据对象
        """
        from utils.logger import get_logger
        logger = get_logger()
        
        logger.info(f"[MetadataRepository] create_or_update: image_id={image_id}")
        logger.info(f"[MetadataRepository] xmp_data keys: {list(xmp_data.keys())}")
        logger.info(f"[MetadataRepository] ai_analysis in xmp_data: {'ai_analysis' in xmp_data}")
        logger.info(f"[MetadataRepository] evaluations in xmp_data: {'evaluations' in xmp_data}")
        
        # 检查是否已存在
        existing = self.find_by_image_id(image_id)
        
        if existing:
            # 更新现有记录
            existing.xmp_rating = xmp_data.get('rating') if 'rating' in xmp_data else existing.xmp_rating
            existing.xmp_label = xmp_data.get('label') if 'label' in xmp_data else existing.xmp_label
            if 'subjects' in xmp_data:
                existing.xmp_subjects = ';'.join(xmp_data.get('subjects', []))
            existing.xmp_description = xmp_data.get('description') if 'description' in xmp_data else existing.xmp_description
            if 'ai_analysis' in xmp_data:
                existing.ai_analysis = xmp_data.get('ai_analysis')
            if 'evaluations' in xmp_data:
                existing.evaluations = xmp_data.get('evaluations')
            existing.updated_at = datetime.now()
            logger.info(
                f"[MetadataRepository] Updating existing metadata | "
                f"image_id={image_id} | "
                f"has_ai_analysis={bool(existing.ai_analysis)} | "
                f"has_evaluations={bool(existing.evaluations)}"
            )
            return self.update(existing)
        
        # 创建新记录
        metadata = Metadata(
            image_id=image_id,
            xmp_rating=xmp_data.get('rating'),
            xmp_label=xmp_data.get('label'),
            xmp_subjects=';'.join(xmp_data.get('subjects', [])) if xmp_data.get('subjects') else None,
            xmp_description=xmp_data.get('description'),
            ai_analysis=xmp_data.get('ai_analysis'),
            evaluations=xmp_data.get('evaluations')
        )
        
        logger.info(
            f"[MetadataRepository] Creating new metadata | "
            f"image_id={image_id} | "
            f"has_ai_analysis={bool(metadata.ai_analysis)} | "
            f"has_evaluations={bool(metadata.evaluations)}"
        )
        
        with self.db.transaction() as conn:
            cursor = conn.execute(
                f"""
                INSERT INTO {Metadata.TABLE_NAME}
                (image_id, xmp_rating, xmp_label, xmp_subjects, xmp_description, ai_analysis, evaluations)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metadata.image_id,
                    metadata.xmp_rating,
                    metadata.xmp_label,
                    metadata.xmp_subjects,
                    metadata.xmp_description,
                    metadata.ai_analysis,
                    metadata.evaluations
                )
            )
            metadata.id = cursor.lastrowid
        
        logger.info(
            f"[MetadataRepository] New metadata created | "
            f"id={metadata.id} | "
            f"image_id={metadata.image_id}"
        )
        return metadata
    
    def find_by_id(self, metadata_id: int) -> Optional[Metadata]:
        """根据ID查找元数据"""
        cursor = self.db.execute(
            f"SELECT * FROM {Metadata.TABLE_NAME} WHERE id = ?",
            (metadata_id,)
        )
        row = cursor.fetchone()
        return Metadata.from_row(row) if row else None
    
    def find_by_image_id(self, image_id: int) -> Optional[Metadata]:
        """根据图像ID查找元数据"""
        cursor = self.db.execute(
            f"SELECT * FROM {Metadata.TABLE_NAME} WHERE image_id = ?",
            (image_id,)
        )
        row = cursor.fetchone()
        return Metadata.from_row(row) if row else None
    
    def update(self, metadata: Metadata) -> Metadata:
        """更新元数据"""
        from utils.logger import get_logger
        logger = get_logger()
        
        metadata.updated_at = datetime.now()
        
        logger.info(
            f"[MetadataRepository] Updating metadata | "
            f"image_id={metadata.image_id} | "
            f"has_ai_analysis={bool(metadata.ai_analysis)} | "
            f"ai_analysis_length={len(metadata.ai_analysis) if metadata.ai_analysis else 0} | "
            f"has_evaluations={bool(metadata.evaluations)}"
        )
        
        with self.db.transaction() as conn:
            conn.execute(
                f"""
                UPDATE {Metadata.TABLE_NAME}
                SET xmp_rating = ?, xmp_label = ?, xmp_subjects = ?,
                    xmp_description = ?, ai_analysis = ?, 
                    evaluations = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    metadata.xmp_rating,
                    metadata.xmp_label,
                    metadata.xmp_subjects,
                    metadata.xmp_description,
                    metadata.ai_analysis,
                    metadata.evaluations,
                    metadata.updated_at.isoformat(),
                    metadata.id
                )
            )
        
        logger.info(
            f"[MetadataRepository] Metadata update completed | "
            f"image_id={metadata.image_id}"
        )
        return metadata
    
    def find_by_rating(self, rating: int) -> List[Metadata]:
        """根据XMP评级查找"""
        cursor = self.db.execute(
            f"SELECT * FROM {Metadata.TABLE_NAME} WHERE xmp_rating = ?",
            (rating,)
        )
        return [Metadata.from_row(row) for row in cursor.fetchall()]
    
    def find_by_label(self, label: str) -> List[Metadata]:
        """根据XMP标签查找"""
        cursor = self.db.execute(
            f"SELECT * FROM {Metadata.TABLE_NAME} WHERE xmp_label = ?",
            (label,)
        )
        return [Metadata.from_row(row) for row in cursor.fetchall()]
    
    def find_by_subject(self, subject: str) -> List[Metadata]:
        """根据XMP关键词查找"""
        cursor = self.db.execute(
            f"SELECT * FROM {Metadata.TABLE_NAME} WHERE xmp_subjects LIKE ?",
            (f'%{subject}%',)
        )
        return [Metadata.from_row(row) for row in cursor.fetchall()]
    
    def delete_by_image_id(self, image_id: int) -> bool:
        """
        根据图像ID删除元数据记录
        
        Args:
            image_id: 图像ID
            
        Returns:
            是否删除成功
        """
        with self.db.transaction() as conn:
            cursor = conn.execute(
                f"DELETE FROM {Metadata.TABLE_NAME} WHERE image_id = ?",
                (image_id,)
            )
            return cursor.rowcount > 0
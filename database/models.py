"""数据库模型"""
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class Image:
    """图像模型"""
    
    TABLE_NAME = "images"
    
    def __init__(self, 
                 id: Optional[int] = None,
                 file_path: str = "",
                 file_name: str = "",
                 file_size: int = 0,
                 file_hash: Optional[str] = None,
                 width: Optional[int] = None,
                 height: Optional[int] = None,
                 format: Optional[str] = None,
                 thumbnail_path: Optional[str] = None,
                 original_path: Optional[str] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 deleted_at: Optional[datetime] = None):
        self.id = id
        self.file_path = file_path
        self.file_name = file_name
        self.file_size = file_size
        self.file_hash = file_hash
        self.width = width
        self.height = height
        self.format = format
        self.thumbnail_path = thumbnail_path
        self.original_path = original_path or file_path  # 默认使用file_path
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.deleted_at = deleted_at
    
    @classmethod
    def create_table(cls, db: 'DatabaseConnection'):
        """创建图像表"""
        db.execute(f"""
            CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_hash TEXT,
                width INTEGER,
                height INTEGER,
                format TEXT,
                thumbnail_path TEXT,
                original_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP
            )
        """)
        db.execute(f"CREATE INDEX IF NOT EXISTS idx_file_path ON {cls.TABLE_NAME}(file_path)")
        db.execute(f"CREATE INDEX IF NOT EXISTS idx_file_hash ON {cls.TABLE_NAME}(file_hash)")
        db.execute(f"CREATE INDEX IF NOT EXISTS idx_deleted_at ON {cls.TABLE_NAME}(deleted_at)")
        db.get_connection().commit()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'width': self.width,
            'height': self.height,
            'format': self.format,
            'thumbnail_path': self.thumbnail_path,
            'original_path': self.original_path,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            'deleted_at': self.deleted_at.isoformat() if isinstance(self.deleted_at, datetime) else self.deleted_at,
            'is_deleted': self.deleted_at is not None
        }
    
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Image':
        """从数据库行创建对象"""
        # 兼容旧数据：如果original_path字段不存在，使用file_path
        try:
            original_path = row['original_path'] if row['original_path'] else row['file_path']
        except (KeyError, IndexError):
            original_path = row['file_path']
        
        return cls(
            id=row['id'],
            file_path=row['file_path'],
            file_name=row['file_name'],
            file_size=row['file_size'],
            file_hash=row['file_hash'],
            width=row['width'],
            height=row['height'],
            format=row['format'],
            thumbnail_path=row['thumbnail_path'],
            original_path=original_path,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            deleted_at=datetime.fromisoformat(row['deleted_at']) if row['deleted_at'] else None
        )


class QualityAssessment:
    """质量评估模型"""
    
    TABLE_NAME = "quality_assessments"
    
    def __init__(self,
                 id: Optional[int] = None,
                 image_id: int = 0,
                 quality_score: float = 0.0,
                 rating: int = 1,
                 label: str = "",
                 blur_score: Optional[float] = None,
                 brightness: Optional[float] = None,
                 entropy: Optional[float] = None,
                 brisque: Optional[float] = None,
                 aesthetic_score: Optional[float] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        self.id = id
        self.image_id = image_id
        self.quality_score = quality_score
        self.rating = rating
        self.label = label
        self.blur_score = blur_score
        self.brightness = brightness
        self.entropy = entropy
        self.brisque = brisque
        self.aesthetic_score = aesthetic_score
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    @classmethod
    def create_table(cls, db: 'DatabaseConnection'):
        """创建质量评估表"""
        db.execute(f"""
            CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                quality_score REAL NOT NULL,
                rating INTEGER NOT NULL,
                label TEXT NOT NULL,
                blur_score REAL,
                brightness REAL,
                entropy REAL,
                brisque REAL,
                aesthetic_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
                UNIQUE(image_id)
            )
        """)
        db.execute(f"CREATE INDEX IF NOT EXISTS idx_image_id ON {cls.TABLE_NAME}(image_id)")
        db.execute(f"CREATE INDEX IF NOT EXISTS idx_quality_score ON {cls.TABLE_NAME}(quality_score)")
        db.execute(f"CREATE INDEX IF NOT EXISTS idx_rating ON {cls.TABLE_NAME}(rating)")
        db.execute(f"CREATE INDEX IF NOT EXISTS idx_label ON {cls.TABLE_NAME}(label)")
        db.get_connection().commit()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'image_id': self.image_id,
            'quality_score': self.quality_score,
            'rating': self.rating,
            'label': self.label,
            'blur_score': self.blur_score,
            'brightness': self.brightness,
            'entropy': self.entropy,
            'brisque': self.brisque,
            'aesthetic_score': self.aesthetic_score,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
    
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'QualityAssessment':
        """从数据库行创建对象"""
        return cls(
            id=row['id'],
            image_id=row['image_id'],
            quality_score=row['quality_score'],
            rating=row['rating'],
            label=row['label'],
            blur_score=row['blur_score'],
            brightness=row['brightness'],
            entropy=row['entropy'],
            brisque=row['brisque'],
            aesthetic_score=row['aesthetic_score'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )


class Metadata:
    """元数据模型"""
    
    TABLE_NAME = "metadata"
    
    def __init__(self,
                 id: Optional[int] = None,
                 image_id: int = 0,
                 xmp_rating: Optional[int] = None,
                 xmp_label: Optional[str] = None,
                 xmp_subjects: Optional[str] = None,  # JSON字符串或分号分隔
                 xmp_description: Optional[str] = None,
                 exif_data: Optional[str] = None,  # JSON字符串
                 ai_analysis: Optional[str] = None,  # AI分析结果
                 evaluations: Optional[str] = None,  # 评估问题数组（JSON格式）
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        self.id = id
        self.image_id = image_id
        self.xmp_rating = xmp_rating
        self.xmp_label = xmp_label
        self.xmp_subjects = xmp_subjects
        self.xmp_description = xmp_description
        self.exif_data = exif_data
        self.ai_analysis = ai_analysis
        self.evaluations = evaluations  # JSON数组格式
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    @classmethod
    def create_table(cls, db: 'DatabaseConnection'):
        """创建元数据表"""
        db.execute(f"""
            CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                xmp_rating INTEGER,
                xmp_label TEXT,
                xmp_subjects TEXT,
                xmp_description TEXT,
                exif_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
                UNIQUE(image_id)
            )
        """)
        db.execute(f"CREATE INDEX IF NOT EXISTS idx_image_id ON {cls.TABLE_NAME}(image_id)")
        db.execute(f"CREATE INDEX IF NOT EXISTS idx_xmp_rating ON {cls.TABLE_NAME}(xmp_rating)")
        db.execute(f"CREATE INDEX IF NOT EXISTS idx_xmp_label ON {cls.TABLE_NAME}(xmp_label)")
        db.get_connection().commit()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        from services.evaluation_service import EvaluationService
        from utils.logger import get_logger
        logger = get_logger()
        
        eval_service = EvaluationService()
        
        # 解析评估问题数组
        logger.debug(f"[Metadata.to_dict] 原始evaluations字段: {self.evaluations}, 类型: {type(self.evaluations)}")
        evaluations_list = eval_service.deserialize_evaluations(self.evaluations)
        logger.debug(f"[Metadata.to_dict] 解析后的evaluations_list: {evaluations_list}, 类型: {type(evaluations_list)}, 长度: {len(evaluations_list) if isinstance(evaluations_list, list) else 'N/A'}")
        
        return {
            'id': self.id,
            'image_id': self.image_id,
            'xmp_rating': self.xmp_rating,
            'xmp_label': self.xmp_label,
            'xmp_subjects': self.xmp_subjects,
            'xmp_description': self.xmp_description,
            'exif_data': self.exif_data,
            'ai_analysis': self.ai_analysis,
            'evaluations': evaluations_list,  # 解析后的数组
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
    
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Metadata':
        """从数据库行创建对象"""
        # 兼容可能不存在的字段
        try:
            ai_analysis = row['ai_analysis'] if row['ai_analysis'] else None
        except (KeyError, IndexError):
            ai_analysis = None
        
        try:
            evaluations = row['evaluations'] if row['evaluations'] else None
        except (KeyError, IndexError):
            evaluations = None
        
        return cls(
            id=row['id'],
            image_id=row['image_id'],
            xmp_rating=row['xmp_rating'],
            xmp_label=row['xmp_label'],
            xmp_subjects=row['xmp_subjects'],
            xmp_description=row['xmp_description'],
            exif_data=row['exif_data'],
            ai_analysis=ai_analysis,
            evaluations=evaluations,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )


def create_tables(db: 'DatabaseConnection'):
    """创建所有表"""
    Image.create_table(db)
    QualityAssessment.create_table(db)
    Metadata.create_table(db)

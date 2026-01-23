"""图像数据访问层"""
import hashlib
from pathlib import Path
from typing import Optional, List
from PIL import Image as PILImage

from database.connection import DatabaseConnection
from database.models import Image
from datetime import datetime


class ImageRepository:
    """图像数据访问层"""
    
    def __init__(self, db: DatabaseConnection):
        """
        初始化图像仓库
        
        Args:
            db: 数据库连接
        """
        self.db = db
    
    def create(self, file_path: str) -> Image:
        """
        创建图像记录
        
        Args:
            file_path: 图像文件路径
            
        Returns:
            图像对象
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 计算文件哈希
        file_hash = self._calculate_hash(file_path)
        
        # 获取图像信息
        try:
            with PILImage.open(file_path) as img:
                width, height = img.size
                format = img.format
        except Exception:
            width = height = format = None
        
        # 检查是否已存在
        existing = self.find_by_path(file_path)
        if existing:
            # 更新现有记录
            existing.file_size = path.stat().st_size
            existing.file_hash = file_hash
            existing.width = width
            existing.height = height
            existing.format = format
            return self.update(existing)
        
        # 创建新记录
        image = Image(
            file_path=str(path.absolute()),
            file_name=path.name,
            file_size=path.stat().st_size,
            file_hash=file_hash,
            width=width,
            height=height,
            format=format,
            original_path=str(path.absolute())  # 记录原路径
        )
        
        with self.db.transaction() as conn:
            cursor = conn.execute(
                f"""
                INSERT INTO {Image.TABLE_NAME} 
                (file_path, file_name, file_size, file_hash, width, height, format, original_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    image.file_path,
                    image.file_name,
                    image.file_size,
                    image.file_hash,
                    image.width,
                    image.height,
                    image.format,
                    image.original_path
                )
            )
            image.id = cursor.lastrowid
        
        return image
    
    def find_by_id(self, image_id: int) -> Optional[Image]:
        """根据ID查找图像"""
        cursor = self.db.execute(
            f"SELECT * FROM {Image.TABLE_NAME} WHERE id = ?",
            (image_id,)
        )
        row = cursor.fetchone()
        return Image.from_row(row) if row else None
    
    def find_by_path(self, file_path: str) -> Optional[Image]:
        """根据路径查找图像"""
        path = str(Path(file_path).absolute())
        cursor = self.db.execute(
            f"SELECT * FROM {Image.TABLE_NAME} WHERE file_path = ?",
            (path,)
        )
        row = cursor.fetchone()
        return Image.from_row(row) if row else None
    
    def find_by_hash(self, file_hash: str) -> Optional[Image]:
        """根据哈希查找图像"""
        cursor = self.db.execute(
            f"SELECT * FROM {Image.TABLE_NAME} WHERE file_hash = ?",
            (file_hash,)
        )
        row = cursor.fetchone()
        return Image.from_row(row) if row else None
    
    def update(self, image: Image) -> Image:
        """更新图像记录"""
        image.updated_at = datetime.now()
        
        with self.db.transaction() as conn:
            conn.execute(
                f"""
                UPDATE {Image.TABLE_NAME}
                SET file_name = ?, file_size = ?, file_hash = ?, 
                    width = ?, height = ?, format = ?, original_path = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    image.file_name,
                    image.file_size,
                    image.file_hash,
                    image.width,
                    image.height,
                    image.format,
                    image.original_path,
                    image.updated_at.isoformat(),
                    image.id
                )
            )
        
        return image
    
    def soft_delete(self, image_id: int) -> bool:
        """软删除（移动到回收站文件夹，保留目录结构）"""
        image = self.find_by_id(image_id)
        if not image or image.deleted_at:
            return False
        
        from config.settings import get_settings
        from shutil import move
        import os
        
        settings = get_settings()
        trash_dir = Path(settings.trash.trash_dir)
        trash_dir.mkdir(parents=True, exist_ok=True)
        
        original_path = Path(image.original_path or image.file_path)
        if not original_path.exists():
            # 文件不存在，只更新数据库
            with self.db.transaction() as conn:
                conn.execute(
                    f"""
                    UPDATE {Image.TABLE_NAME}
                    SET deleted_at = ?
                    WHERE id = ?
                    """,
                    (datetime.now().isoformat(), image_id)
                )
            return True
        
        # 计算回收站路径（保留目录结构）
        if settings.trash.preserve_structure:
            # 获取相对路径（从原路径的根目录开始）
            # 如果原路径是绝对路径，尝试找到共同根目录
            try:
                # 尝试从原路径中提取相对路径结构
                # 例如：F:\照片\2024\01\image.jpg -> trash\F_\照片\2024\01\image.jpg
                # 或者更简单：保留驱动器号和路径结构
                path_parts = original_path.parts
                # 移除驱动器号（Windows）或根目录（Linux）
                if len(path_parts) > 1:
                    # 保留从第一个目录开始的结构
                    relative_parts = path_parts[1:] if path_parts[0].endswith(':') else path_parts
                    # 将驱动器号转换为目录名（Windows）
                    if path_parts[0].endswith(':'):
                        drive_name = path_parts[0].replace(':', '_')
                        relative_parts = [drive_name] + list(relative_parts)
                else:
                    relative_parts = [original_path.name]
                
                trash_path = trash_dir / Path(*relative_parts)
            except Exception:
                # 如果计算失败，使用文件名
                trash_path = trash_dir / original_path.name
        else:
            # 不保留结构，直接放到回收站根目录
            trash_path = trash_dir / original_path.name
        
        # 确保目标目录存在
        trash_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果目标文件已存在，添加序号
        counter = 1
        base_trash_path = trash_path
        while trash_path.exists():
            stem = base_trash_path.stem
            suffix = base_trash_path.suffix
            trash_path = base_trash_path.parent / f"{stem}_{counter}{suffix}"
            counter += 1
        
        try:
            # 移动文件到回收站
            move(str(original_path), str(trash_path))
            
            # 更新数据库：记录新路径和原路径
            with self.db.transaction() as conn:
                conn.execute(
                    f"""
                    UPDATE {Image.TABLE_NAME}
                    SET file_path = ?, original_path = ?, deleted_at = ?
                    WHERE id = ?
                    """,
                    (str(trash_path.absolute()), str(original_path.absolute()), 
                     datetime.now().isoformat(), image_id)
                )
            
            return True
        except Exception as e:
            # 移动失败，记录错误但不阻止删除标记
            from utils.logger import get_logger
            logger = get_logger()
            logger.error(f"移动文件到回收站失败: {e}", exc_info=True)
            # 仍然标记为删除
            with self.db.transaction() as conn:
                conn.execute(
                    f"""
                    UPDATE {Image.TABLE_NAME}
                    SET deleted_at = ?
                    WHERE id = ?
                    """,
                    (datetime.now().isoformat(), image_id)
                )
            return True
    
    def restore(self, image_id: int) -> bool:
        """从回收站恢复（移回原路径）"""
        image = self.find_by_id(image_id)
        if not image or not image.deleted_at:
            return False
        
        if not image.original_path:
            # 没有原路径记录，无法恢复
            return False
        
        from shutil import move
        from config.settings import get_settings
        
        original_path = Path(image.original_path)
        current_path = Path(image.file_path)
        
        # 确保原路径的目录存在
        original_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果原路径已存在文件，添加序号
        counter = 1
        base_original_path = original_path
        while original_path.exists():
            stem = base_original_path.stem
            suffix = base_original_path.suffix
            original_path = base_original_path.parent / f"{stem}_{counter}{suffix}"
            counter += 1
        
        try:
            # 移动文件回原路径
            if current_path.exists():
                move(str(current_path), str(original_path))
            
            # 更新数据库
            with self.db.transaction() as conn:
                conn.execute(
                    f"""
                    UPDATE {Image.TABLE_NAME}
                    SET file_path = ?, deleted_at = NULL
                    WHERE id = ?
                    """,
                    (str(original_path.absolute()), image_id)
                )
            
            return True
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger()
            logger.error(f"恢复文件失败: {e}", exc_info=True)
            return False
    
    def hard_delete(self, image_id: int) -> bool:
        """硬删除（永久删除）"""
        with self.db.transaction() as conn:
            cursor = conn.execute(
                f"DELETE FROM {Image.TABLE_NAME} WHERE id = ?",
                (image_id,)
            )
            return cursor.rowcount > 0
    
    def list_deleted(self, limit: Optional[int] = None, offset: int = 0) -> List[Image]:
        """列出已删除的图像（回收站）"""
        query = f"SELECT * FROM {Image.TABLE_NAME} WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC"
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        cursor = self.db.execute(query)
        return [Image.from_row(row) for row in cursor.fetchall()]
    
    def count_deleted(self) -> int:
        """统计已删除图像数量"""
        cursor = self.db.execute(f"SELECT COUNT(*) as count FROM {Image.TABLE_NAME} WHERE deleted_at IS NOT NULL")
        row = cursor.fetchone()
        return row['count'] if row else 0
    
    def delete(self, image_id: int) -> bool:
        """删除图像记录（级联删除相关记录）"""
        with self.db.transaction() as conn:
            cursor = conn.execute(
                f"DELETE FROM {Image.TABLE_NAME} WHERE id = ?",
                (image_id,)
            )
            return cursor.rowcount > 0
    
    def list_all(self, limit: Optional[int] = None, offset: int = 0, include_deleted: bool = False) -> List[Image]:
        """列出所有图像"""
        if include_deleted:
            query = f"SELECT * FROM {Image.TABLE_NAME} ORDER BY created_at DESC"
        else:
            query = f"SELECT * FROM {Image.TABLE_NAME} WHERE deleted_at IS NULL ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        cursor = self.db.execute(query)
        return [Image.from_row(row) for row in cursor.fetchall()]
    
    def count(self) -> int:
        """统计图像数量"""
        cursor = self.db.execute(f"SELECT COUNT(*) as count FROM {Image.TABLE_NAME}")
        row = cursor.fetchone()
        return row['count'] if row else 0
    
    @staticmethod
    def _calculate_hash(file_path: str, chunk_size: int = 8192) -> str:
        """计算文件MD5哈希"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

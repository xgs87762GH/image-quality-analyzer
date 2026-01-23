"""图像数据访问层"""
import hashlib
from pathlib import Path
from typing import Optional, List
from datetime import datetime
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
        """
        软删除（移动到回收站）
        
        参考 digiKam 实现方式：
        1. 将文件移动到回收站目录（保留目录结构）
        2. 在数据库中标记为已删除（deleted_at）
        3. 保留原始路径信息（original_path）用于恢复
        
        Args:
            image_id: 图像ID
            
        Returns:
            是否删除成功
            
        Raises:
            Exception: 删除失败时抛出异常
        """
        from utils.logger import get_logger
        from services.trash_service import TrashManager
        
        logger = get_logger()
        
        # 查找图像
        image = self.find_by_id(image_id)
        if not image or image.deleted_at:
            logger.warning(f"[软删除] 图像不存在或已被删除: image_id={image_id}")
            return False
        
        # 初始化回收站管理器
        trash_manager = TrashManager()
        
        # 确定要移动的文件路径
        # 优先使用 original_path（原始位置），如果不存在则使用 file_path（当前位置）
        source_path = None
        if image.original_path:
            original_path = Path(image.original_path).resolve()
            if original_path.exists():
                source_path = original_path
                logger.debug(f"[软删除] 使用 original_path: {original_path}")
        
        if not source_path and image.file_path:
            file_path = Path(image.file_path).resolve()
            if file_path.exists():
                source_path = file_path
                logger.debug(f"[软删除] 使用 file_path: {file_path}")
        
        # 记录原始位置（用于恢复）
        original_location = str(source_path.absolute()) if source_path else None
        
        if not source_path:
            # 文件不存在，只更新数据库标记
            logger.warning(f"[软删除] 文件不存在，仅更新数据库: image_id={image_id}, original_path={image.original_path}, file_path={image.file_path}")
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
        
        try:
            # 使用回收站管理器移动文件
            trash_path, saved_original_location = trash_manager.move_to_trash(
                source_path, 
                original_location
            )
            
            # 更新数据库：记录新路径和原路径
            with self.db.transaction() as conn:
                conn.execute(
                    f"""
                    UPDATE {Image.TABLE_NAME}
                    SET file_path = ?, original_path = ?, deleted_at = ?
                    WHERE id = ?
                    """,
                    (str(trash_path.absolute()), saved_original_location, 
                     datetime.now().isoformat(), image_id)
                )
            
            logger.info(f"[软删除] 数据库已更新: image_id={image_id}, new_path={trash_path}, original_path={saved_original_location}")
            return True
            
        except FileNotFoundError:
            # 文件不存在，只更新数据库标记
            logger.warning(f"[软删除] 文件不存在，仅更新数据库: image_id={image_id}")
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
        except Exception as e:
            # 其他错误：记录并重新抛出
            logger.error(f"[软删除] 删除失败: image_id={image_id}, 错误: {e}", exc_info=True)
            raise
    
    def restore(self, image_id: int) -> bool:
        """
        从回收站恢复图像
        
        参考 digiKam 实现方式：
        1. 将文件从回收站移回原始位置
        2. 清除数据库中的删除标记（deleted_at = NULL）
        3. 更新文件路径为恢复后的路径
        
        Args:
            image_id: 图像ID
            
        Returns:
            是否恢复成功
            
        Raises:
            Exception: 恢复失败时抛出异常
        """
        from utils.logger import get_logger
        from services.trash_service import TrashManager
        
        logger = get_logger()
        
        # 查找图像
        image = self.find_by_id(image_id)
        if not image or not image.deleted_at:
            logger.warning(f"[恢复] 图像不存在或未被删除: image_id={image_id}")
            return False
        
        if not image.original_path:
            logger.error(f"[恢复] 没有原始路径记录，无法恢复: image_id={image_id}")
            return False
        
        # 初始化回收站管理器
        trash_manager = TrashManager()
        
        current_path = Path(image.file_path).resolve()
        original_path = Path(image.original_path).resolve()
        
        try:
            # 使用回收站管理器恢复文件
            restored_path = trash_manager.restore_from_trash(current_path, original_path)
            
            # 更新数据库：清除删除标记，更新文件路径
            with self.db.transaction() as conn:
                conn.execute(
                    f"""
                    UPDATE {Image.TABLE_NAME}
                    SET file_path = ?, original_path = ?, deleted_at = NULL
                    WHERE id = ?
                    """,
                    (str(restored_path.absolute()), str(restored_path.absolute()), image_id)
                )
            
            logger.info(f"[恢复] 数据库已更新: image_id={image_id}, restored_path={restored_path}")
            return True
            
        except FileNotFoundError as e:
            logger.error(f"[恢复] 文件不存在: image_id={image_id}, current_path={current_path}, 错误: {e}", exc_info=True)
            # 即使文件不存在，也清除删除标记（可能是文件已被手动删除）
            with self.db.transaction() as conn:
                conn.execute(
                    f"""
                    UPDATE {Image.TABLE_NAME}
                    SET deleted_at = NULL
                    WHERE id = ?
                    """,
                    (image_id,)
                )
            logger.warning(f"[恢复] 文件不存在，仅清除删除标记: image_id={image_id}")
            return False
        except Exception as e:
            logger.error(f"[恢复] 恢复失败: image_id={image_id}, 错误: {e}", exc_info=True)
            raise
    
    def hard_delete(self, image_id: int) -> bool:
        """
        硬删除（永久删除文件和数据库记录）
        参考图片管理软件的删除逻辑：删除文件 + 删除数据库记录 + 删除关联数据
        """
        image = self.find_by_id(image_id)
        if not image:
            return False
        
        from utils.logger import get_logger
        logger = get_logger()
        
        # 1. 删除物理文件（如果存在）
        file_paths_to_delete = []
        if image.file_path:
            file_paths_to_delete.append(Path(image.file_path))
        if image.original_path and image.original_path != image.file_path:
            file_paths_to_delete.append(Path(image.original_path))
        
        for file_path in file_paths_to_delete:
            if file_path.exists():
                try:
                    file_path.unlink()  # 删除文件
                    logger.info(f"[硬删除] 已删除文件: {file_path}")
                except Exception as e:
                    logger.error(f"[硬删除] 删除文件失败: {file_path}, 错误: {e}", exc_info=True)
                    # 继续删除数据库记录，即使文件删除失败
        
        # 2. 删除关联数据（质量评估、元数据）
        from repositories.quality_repository import QualityRepository
        from repositories.metadata_repository import MetadataRepository
        
        quality_repo = QualityRepository(self.db)
        metadata_repo = MetadataRepository(self.db)
        
        try:
            quality_repo.delete_by_image_id(image_id)
            metadata_repo.delete_by_image_id(image_id)
        except Exception as e:
            logger.warning(f"[硬删除] 删除关联数据失败: {e}", exc_info=True)
        
        # 3. 删除数据库记录
        with self.db.transaction() as conn:
            cursor = conn.execute(
                f"DELETE FROM {Image.TABLE_NAME} WHERE id = ?",
                (image_id,)
            )
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"[硬删除] 已删除数据库记录: image_id={image_id}")
            return deleted
    
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

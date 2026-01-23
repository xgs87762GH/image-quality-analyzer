"""图像服务（业务逻辑层）"""
from pathlib import Path
from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from analyzers.ai_analyzer import AIAnalyzer

from database.connection import get_db
from repositories.image_repository import ImageRepository
from repositories.quality_repository import QualityRepository
from repositories.metadata_repository import MetadataRepository
from analyzers.image_analyzer import ImageAnalyzer
from metadata.xmp_writer import XMPWriter
from utils.logger import get_logger
from config.settings import get_settings


class ImageService:
    """图像服务 - 整合图像分析、存储和元数据操作"""
    
    def __init__(self, use_aesthetic: bool = False, aesthetic_mode: str = 'none',
                 ai_analyzer: Optional[Any] = None):
        """
        初始化图像服务
        
        Args:
            use_aesthetic: 是否启用审美评分（向后兼容）
            aesthetic_mode: 审美评估方式 ('none', 'clip', 'ai')
            ai_analyzer: AI分析器实例（当aesthetic_mode='ai'时需要）
        """
        settings = get_settings()
        self.db = get_db()
        self.image_repo = ImageRepository(self.db)
        self.quality_repo = QualityRepository(self.db)
        self.metadata_repo = MetadataRepository(self.db)
        self.analyzer = ImageAnalyzer(
            use_aesthetic=use_aesthetic,
            aesthetic_mode=aesthetic_mode,
            ai_analyzer=ai_analyzer
        )
        # 使用ExifTool管理器自动检测最佳路径（优先使用项目内的ExifTool）
        self.xmp_writer = XMPWriter()  # 自动检测项目内或系统PATH中的ExifTool
        self.logger = get_logger()
    
    def process_image(self, file_path: str, write_xmp: bool = True) -> Dict[str, Any]:
        """
        处理单张图像：分析、存储到数据库、写入XMP
        
        Args:
            file_path: 图像文件路径
            write_xmp: 是否写入XMP元数据
            
        Returns:
            处理结果字典
        """
        try:
            # 1. 创建或获取图像记录
            self.logger.info(f"处理图像: {file_path}")
            image = self.image_repo.create(file_path)
            self.logger.debug(f"图像记录已创建/更新: ID={image.id}")
            
            # 2. 分析图像质量
            analysis = self.analyzer.analyze(file_path)
            if not analysis:
                self.logger.warning(f"图像分析失败: {file_path}")
                return {'success': False, 'error': '分析失败'}
            
            # 3. 保存质量评估到数据库
            quality_assessment = self.quality_repo.create_or_update(
                image.id,
                analysis
            )
            self.logger.debug(f"质量评估已保存: ID={quality_assessment.id}")
            
            # 4. 保存元数据到数据库
            xmp_data = {
                'rating': analysis['rating'],
                'label': analysis['label'],
                'subjects': analysis['subjects'],
                'description': f"QualityAnalysis: {analysis['metrics']}"
            }
            metadata = self.metadata_repo.create_or_update(image.id, xmp_data)
            self.logger.debug(f"元数据已保存: ID={metadata.id}")
            
            # 5. 写入XMP元数据（如果启用）
            if write_xmp and self.xmp_writer.is_available():
                settings = get_settings()
                success = self.xmp_writer.write(
                    file_path,
                    analysis,
                    backup=settings.metadata.backup_original
                )
                if success:
                    self.logger.debug(f"XMP元数据已写入: {file_path}")
                else:
                    self.logger.warning(f"XMP元数据写入失败: {file_path}")
            
            return {
                'success': True,
                'image_id': image.id,
                'quality_score': analysis['quality_score'],
                'rating': analysis['rating'],
                'label': analysis['label']
            }
        except Exception as e:
            self.logger.error(f"处理图像时出错 {file_path}: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def get_image_info(self, image_id: int) -> Optional[Dict[str, Any]]:
        """
        获取图像完整信息（包括质量和元数据）
        
        Args:
            image_id: 图像ID
            
        Returns:
            图像信息字典，如果不存在则返回None
        """
        image = self.image_repo.find_by_id(image_id)
        if not image:
            return None
        
        quality = self.quality_repo.find_by_image_id(image_id)
        metadata = self.metadata_repo.find_by_image_id(image_id)
        
        result = image.to_dict()
        if quality:
            result['quality'] = quality.to_dict()
        if metadata:
            metadata_dict = metadata.to_dict()
            result['metadata'] = metadata_dict
            
            # 将评估结果也添加到顶层
            if metadata_dict.get('evaluations'):
                result['evaluations'] = metadata_dict['evaluations']
            
            if metadata.ai_analysis:
                result['ai_analysis'] = metadata.ai_analysis
        
        return result
    
    def find_duplicates(self) -> List[Dict[str, Any]]:
        """
        查找重复图像（基于文件哈希）
        
        Returns:
            重复图像列表
        """
        # 查询有相同哈希的图像
        cursor = self.db.execute(
            """
            SELECT file_hash, COUNT(*) as count, GROUP_CONCAT(id) as image_ids
            FROM images
            WHERE file_hash IS NOT NULL
            GROUP BY file_hash
            HAVING count > 1
            """
        )
        
        duplicates = []
        for row in cursor.fetchall():
            image_ids = [int(id) for id in row['image_ids'].split(',')]
            images = [self.image_repo.find_by_id(id) for id in image_ids]
            duplicates.append({
                'hash': row['file_hash'],
                'count': row['count'],
                'images': [img.to_dict() for img in images if img]
            })
        
        return duplicates
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_images = self.image_repo.count()
        quality_stats = self.quality_repo.get_statistics()
        
        return {
            'total_images': total_images,
            'quality_statistics': quality_stats
        }

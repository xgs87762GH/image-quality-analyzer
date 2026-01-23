"""自动导入服务（高内聚、低耦合）"""
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from processors.batch_processor import BatchProcessor


class AutoImportService:
    """自动导入服务 - 负责从配置目录自动导入图片"""
    
    def __init__(self):
        """初始化自动导入服务"""
        self.logger = get_logger()
        self.processor = BatchProcessor(use_aesthetic=False)
    
    def validate_directories(self, directories: List[str]) -> Dict[str, Any]:
        """
        验证目录列表
        
        Args:
            directories: 目录路径列表
            
        Returns:
            验证结果字典，包含有效和无效目录
        """
        valid_directories = []
        invalid_directories = []
        
        for directory in directories:
            dir_path = Path(directory)
            if dir_path.exists() and dir_path.is_dir():
                valid_directories.append(directory)
            else:
                invalid_directories.append(directory)
                self.logger.warning(f"[自动导入] 目录不存在或无效: {directory}")
        
        return {
            'valid_directories': valid_directories,
            'invalid_directories': invalid_directories,
            'valid_count': len(valid_directories),
            'invalid_count': len(invalid_directories)
        }
    
    def import_from_directories(self, directories: List[str], 
                                silent: bool = False) -> Dict[str, Any]:
        """
        从目录列表导入图片
        
        Args:
            directories: 目录路径列表
            silent: 是否静默模式（不输出详细信息）
            
        Returns:
            导入结果字典
        """
        if not directories:
            return {
                'success': True,
                'total': 0,
                'success_count': 0,
                'failed_count': 0,
                'message': '没有需要导入的目录'
            }
        
        # 验证目录
        validation = self.validate_directories(directories)
        valid_dirs = validation['valid_directories']
        invalid_dirs = validation['invalid_directories']
        
        if invalid_dirs:
            self.logger.warning(f"[自动导入] 发现 {len(invalid_dirs)} 个无效目录")
        
        if not valid_dirs:
            return {
                'success': False,
                'error': f'所有目录都不存在或无效',
                'invalid_directories': invalid_dirs,
                'total': 0,
                'success_count': 0,
                'failed_count': 0
            }
        
        # 执行导入
        if not silent:
            self.logger.info(f"[自动导入] 开始导入，有效目录数量: {len(valid_dirs)}")
        
        try:
            results = self.processor.process(
                input_dir=None,
                input_dirs=valid_dirs,
                output_csv=None,
                write_xmp=False
            )
            
            # 统计结果
            success_count = len([r for r in results if r.get('image_id')])
            total_count = len(results)
            failed_count = total_count - success_count
            
            message = f'导入完成：成功 {success_count}/{total_count} 张'
            if invalid_dirs:
                message += f'，{len(invalid_dirs)} 个目录无效已跳过'
            
            if not silent:
                self.logger.info(f"[自动导入] {message}")
            
            return {
                'success': True,
                'message': message,
                'total': total_count,
                'success_count': success_count,
                'failed_count': failed_count,
                'invalid_directories': invalid_dirs if invalid_dirs else []
            }
        except Exception as e:
            self.logger.error(f"[自动导入] 导入失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'total': 0,
                'success_count': 0,
                'failed_count': 0
            }

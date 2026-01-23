"""批量图像处理器（使用数据库）"""
import csv
from pathlib import Path
from typing import List, Optional

from services.image_service import ImageService
from utils.constants import DEFAULT_IMAGE_EXTENSIONS
from utils.logger import get_logger
from config.settings import get_settings


class BatchProcessor:
    """批量图像处理器 - 使用数据库存储"""
    
    def __init__(self, use_aesthetic: bool = False):
        """
        初始化批量处理器
        
        Args:
            use_aesthetic: 是否启用审美评分
        """
        self.image_service = ImageService(use_aesthetic=use_aesthetic)
        self.logger = get_logger()
        settings = get_settings()
        self.write_xmp = settings.metadata.write_to_xmp
    
    def _collect_image_files(self, input_dir: str, extensions: List[str]) -> List[Path]:
        """
        收集图像文件
        
        Args:
            input_dir: 输入目录
            extensions: 图像扩展名列表
            
        Returns:
            图像文件路径列表
        """
        input_path = Path(input_dir)
        image_files = []
        seen_files = set()
        
        for ext in extensions:
            # 小写扩展名
            for img_file in input_path.rglob(f"*{ext}"):
                if img_file not in seen_files:
                    image_files.append(img_file)
                    seen_files.add(img_file)
            # 大写扩展名
            for img_file in input_path.rglob(f"*{ext.upper()}"):
                if img_file not in seen_files:
                    image_files.append(img_file)
                    seen_files.add(img_file)
        
        return image_files
    
    def process(self, input_dir: str, output_csv: Optional[str] = None,
                extensions: Optional[List[str]] = None, 
                write_xmp: Optional[bool] = None,
                input_dirs: Optional[List[str]] = None) -> List[dict]:
        """
        批量处理图像（保存到数据库）
        
        Args:
            input_dir: 输入目录
            output_csv: 输出CSV文件路径（可选，用于导出）
            extensions: 图像扩展名列表（默认使用DEFAULT_IMAGE_EXTENSIONS）
            write_xmp: 是否写入XMP元数据（默认使用配置）
            
        Returns:
            处理结果列表
        """
        settings = get_settings()
        if extensions is None:
            extensions = settings.image_extensions
        
        # 支持多目录
        input_dirs_list = []
        if input_dirs:
            input_dirs_list = input_dirs
        elif input_dir:
            input_dirs_list = [input_dir]
        else:
            self.logger.error("未指定输入目录")
            print("错误: 未指定输入目录")
            return []
        
        # 收集所有目录的图像文件
        image_files = []
        for dir_path in input_dirs_list:
            input_path = Path(dir_path)
            if not input_path.exists():
                self.logger.warning(f"目录不存在: {dir_path}")
                print(f"警告: 目录不存在: {dir_path}")
                continue
            
            # 收集图像文件
            dir_files = self._collect_image_files(dir_path, extensions)
            image_files.extend(dir_files)
        self.logger.info(f"找到 {len(image_files)} 个图像文件")
        print(f"找到 {len(image_files)} 个图像文件")
        
        # 处理结果
        results = []
        success_count = 0
        fail_count = 0
        
        for i, img_path in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] 处理: {img_path.name}")
            
            # 使用服务层处理图像
            result = self.image_service.process_image(
                str(img_path),
                write_xmp=write_xmp if write_xmp is not None else self.write_xmp
            )
            
            if result.get('success'):
                success_count += 1
                print(f"  质量分数: {result.get('quality_score', 0):.2f}")
                print(f"  评级: {result.get('rating', 0)} 星")
                print(f"  标签: {result.get('label', '')}")
                print(f"  ✓ 已保存到数据库")
                
                # 获取完整信息
                image_info = self.image_service.get_image_info(result['image_id'])
                if image_info:
                    results.append({
                        "file": str(img_path),
                        "image_id": result['image_id'],
                        **image_info.get('quality', {})
                    })
            else:
                fail_count += 1
                error = result.get('error', '未知错误')
                print(f"  ✗ 处理失败: {error}")
                self.logger.warning(f"处理失败 {img_path}: {error}")
        
        # 保存CSV报告（如果指定）
        if output_csv and results:
            self._save_csv(output_csv, results)
            print(f"\n结果已导出到: {output_csv}")
        
        # 显示统计信息
        stats = self.image_service.get_statistics()
        print(f"\n处理完成！")
        print(f"  成功: {success_count} 个")
        print(f"  失败: {fail_count} 个")
        print(f"  数据库总记录: {stats.get('total_images', 0)} 个")
        
        return results
    
    def _save_csv(self, output_path: str, results: List[dict]):
        """保存结果到CSV文件"""
        if not results:
            return
        
        # 展平嵌套字典
        flattened_results = []
        for result in results:
            flat = {
                'file': result.get('file', ''),
                'image_id': result.get('image_id', ''),
                'quality_score': result.get('quality_score', 0),
                'rating': result.get('rating', 0),
                'label': result.get('label', ''),
                'blur_score': result.get('blur_score'),
                'brightness': result.get('brightness'),
                'entropy': result.get('entropy'),
                'brisque': result.get('brisque'),
                'aesthetic_score': result.get('aesthetic_score')
            }
            flattened_results.append(flat)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if flattened_results:
                writer = csv.DictWriter(f, fieldnames=flattened_results[0].keys())
                writer.writeheader()
                writer.writerows(flattened_results)

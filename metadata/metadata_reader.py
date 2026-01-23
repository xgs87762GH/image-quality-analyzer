"""完整元数据读取器 - 读取EXIF、GPS、XMP等所有元数据"""
import json
from typing import Dict
from pathlib import Path
from utils.exiftool_executor import ExifToolExecutor
from utils.logger import get_logger


class MetadataReader:
    """完整元数据读取器 - 使用exiftool读取所有元数据"""
    
    def __init__(self):
        """初始化元数据读取器"""
        self._executor = ExifToolExecutor()
        self._logger = get_logger()
    
    def is_available(self) -> bool:
        """检查exiftool是否可用"""
        return self._executor.is_available()
    
    def read_all(self, image_path: str) -> Dict:
        """
        读取图像的所有元数据（EXIF、GPS、XMP、IPTC等）
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            完整的元数据字典，按类别组织
        """
        if not self.is_available():
            self._logger.warning(f"ExifTool不可用，无法读取元数据: {image_path}")
            return {'error': 'ExifTool不可用'}
        
        if not Path(image_path).exists():
            self._logger.error(f"文件不存在: {image_path}")
            return {'error': '文件不存在'}
        
        self._logger.info(f"开始读取元数据: {image_path}")
        
        try:
            # 确保路径是有效的字符串（处理中文路径编码问题）
            image_path_str = str(image_path)
            # 在Windows上，确保路径使用正确的编码
            if isinstance(image_path, Path):
                # Path对象，直接使用
                image_path_str = str(image_path.resolve())
            else:
                # 字符串路径，确保是有效的UTF-8
                try:
                    image_path_str.encode('utf-8').decode('utf-8')
                except (UnicodeEncodeError, UnicodeDecodeError):
                    # 如果编码失败，尝试修复
                    image_path_str = image_path_str.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
            
            # 使用exiftool读取所有元数据（JSON格式）
            args = [
                "-j",  # JSON输出
                "-G",  # 按组组织（EXIF、GPS、XMP等）
                "-a",  # 复制所有标签（包括重复的）
                "-s",  # 使用短标签名
                image_path_str
            ]
            
            result = self._executor.execute(args, timeout=30)
            
            if not result['success']:
                error_msg = result.get('error', result['stderr'])
                self._logger.error(f"读取元数据失败: {image_path}, 错误: {error_msg}")
                return {'error': f'读取失败: {error_msg}'}
            
            if not result['stdout']:
                self._logger.warning(f"元数据为空: {image_path}")
                return {}
            
            # 解析JSON（确保UTF-8编码）
            try:
                # 确保stdout是UTF-8编码的字符串
                stdout_text = result['stdout']
                if isinstance(stdout_text, bytes):
                    stdout_text = stdout_text.decode('utf-8', errors='replace')
                
                data = json.loads(stdout_text, strict=False)  # strict=False允许控制字符
                if not data or len(data) == 0:
                    self._logger.warning(f"元数据解析结果为空: {image_path}")
                    return {}
                
                # 组织元数据（清理控制字符）
                metadata = data[0]
                organized = self._organize_metadata(metadata)
                
                # 记录成功日志
                categories = [k for k in organized.keys() if k != 'error']
                total_items = sum(len(v) if isinstance(v, dict) else 0 for v in organized.values())
                self._logger.info(
                    f"成功读取元数据: {image_path}, "
                    f"类别数: {len(categories)}, "
                    f"总项数: {total_items}"
                )
                
                return organized
            except json.JSONDecodeError as e:
                self._logger.error(f"JSON解析失败: {image_path}, 错误: {e}")
                return {'error': f'JSON解析失败: {str(e)}'}
        except Exception as e:
            self._logger.error(f"读取元数据异常: {image_path}, 错误: {e}", exc_info=True)
            return {'error': f'读取元数据失败: {str(e)}'}
    
    def _organize_metadata(self, metadata: Dict) -> Dict:
        """组织元数据按类别分类"""
        organized = {
            'file': {},
            'exif': {},
            'gps': {},
            'xmp': {},
            'iptc': {},
            'other': {}
        }
        
        def clean_value(value):
            """清理值中的控制字符和无效编码"""
            if value is None:
                return None
            if isinstance(value, str):
                import re
                # 移除控制字符（保留换行符和制表符）
                value = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', value)
                # 确保是有效的UTF-8
                try:
                    value.encode('utf-8')
                except (UnicodeEncodeError, UnicodeDecodeError):
                    value = value.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
            elif isinstance(value, list):
                return [clean_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: clean_value(v) for k, v in value.items()}
            return value
        
        for key, value in metadata.items():
            if key == 'SourceFile':
                continue
            
            # 清理键和值
            clean_key = clean_value(key) if isinstance(key, str) else key
            clean_val = clean_value(value)
            
            key_str = str(clean_key)
            key_lower = key_str.lower()
            
            if key_lower.startswith('file:'):
                organized['file'][clean_key] = clean_val
            elif key_lower.startswith('exif:') or key_lower.startswith('ifd0:') or key_lower.startswith('ifd1:'):
                organized['exif'][clean_key] = clean_val
            elif key_lower.startswith('gps:'):
                organized['gps'][clean_key] = clean_val
            elif key_lower.startswith('xmp:'):
                organized['xmp'][clean_key] = clean_val
            elif key_lower.startswith('iptc:') or key_lower.startswith('iptc2xmp:'):
                organized['iptc'][clean_key] = clean_val
            else:
                organized['other'][clean_key] = clean_val
        
        return organized

"""XMP元数据写入器"""
import json
from datetime import datetime
from typing import Dict
from utils.constants import XMP_FIELDS
from utils.exiftool_executor import ExifToolExecutor
from utils.logger import get_logger


class XMPWriter:
    """
    XMP元数据写入器 - 使用exiftool，仅写入质量分析相关字段
    
    重要安全特性：
    - 使用-preserve选项保护所有现有元数据
    - 使用+=追加模式，不覆盖原有字段
    - 绝对不写入：个人信息、时间、地点、摄影参数等敏感元数据
    - 仅写入：质量评分、质量标签、分析关键词、元数据修改日期
    """
    
    def __init__(self):
        """初始化XMP写入器"""
        self._executor = ExifToolExecutor()
        self._logger = get_logger()
    
    def is_available(self) -> bool:
        """检查exiftool是否可用"""
        return self._executor.is_available()
    
    def write(self, image_path: str, analysis_result: Dict, backup: bool = True) -> bool:
        """
        将分析结果写入图像XMP元数据（仅写入质量分析相关字段，不覆盖原有元数据）
        
        Args:
            image_path: 图像文件路径
            analysis_result: 分析结果字典
            backup: 是否创建备份
            
        Returns:
            是否成功写入
        """
        if not self.is_available() or not analysis_result:
            self._logger.warning(f"ExifTool不可用或分析结果为空，无法写入XMP: {image_path}")
            return False
        
        self._logger.info(f"开始写入XMP元数据: {image_path}")
        
        try:
            args = ["-preserve"]
            
            if backup:
                args.append("-overwrite_original")
            else:
                args.append("-overwrite_original_in_place")
            
            fields = XMP_FIELDS
            
            # Rating
            if "rating" in analysis_result:
                rating = analysis_result["rating"]
                if rating and rating > 0:
                    args.append(f"-{fields['rating']}+={rating}")
            
            # Label
            if "label" in analysis_result and analysis_result["label"]:
                args.append(f"-{fields['label']}+={analysis_result['label']}")
            
            # MetadataDate
            args.append(f"-{fields['metadata_date']}={datetime.now().isoformat()}")
            
            # Keywords
            all_keywords = []
            if "subjects" in analysis_result:
                subjects = analysis_result["subjects"]
                if isinstance(subjects, list):
                    all_keywords.extend(subjects)
                elif isinstance(subjects, str):
                    all_keywords.extend([s.strip() for s in subjects.split(";") if s.strip()])
            
            if "ai_keywords" in analysis_result:
                ai_keywords = analysis_result["ai_keywords"]
                if isinstance(ai_keywords, list):
                    all_keywords.extend(ai_keywords)
                elif isinstance(ai_keywords, str):
                    all_keywords.extend([k.strip() for k in ai_keywords.split(",") if k.strip()])
            
            if all_keywords:
                unique_keywords = list(dict.fromkeys(all_keywords))
                for keyword in unique_keywords:
                    args.append(f"-{fields['subject']}+={keyword}")
                    args.append(f"-{fields['keywords']}+={keyword}")
            
            # Description
            if "metrics" in analysis_result:
                metrics = analysis_result["metrics"]
                if metrics:
                    metrics_desc = json.dumps(metrics, ensure_ascii=False)
                    if len(metrics_desc) > 300:
                        metrics_desc = metrics_desc[:300] + "..."
                    args.append(f"-{fields['description']}+=[质量分析] {metrics_desc}")
            
            # 确保路径是有效的字符串（处理中文路径编码问题）
            from pathlib import Path
            if isinstance(image_path, Path):
                image_path_str = str(image_path.resolve())
            else:
                image_path_str = str(image_path)
                # 确保是有效的UTF-8
                try:
                    image_path_str.encode('utf-8').decode('utf-8')
                except (UnicodeEncodeError, UnicodeDecodeError):
                    image_path_str = image_path_str.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
            
            args.append(image_path_str)
            
            result = self._executor.execute(args, timeout=30)
            
            if result['success']:
                self._logger.info(f"成功写入XMP元数据: {image_path}")
                return True
            else:
                error_msg = result.get('error', result['stderr'])
                self._logger.error(f"XMP写入失败: {image_path}, 错误: {error_msg}")
                return False
        except Exception as e:
            self._logger.error(f"写入XMP元数据异常: {image_path}, 错误: {e}", exc_info=True)
            return False

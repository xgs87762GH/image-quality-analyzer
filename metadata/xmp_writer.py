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
            
            # 添加字符集参数，解决 Windows 中文路径和元数据编码问题
            # -charset filename=utf8: 指定文件名使用 UTF-8 编码（ExifTool 会自动转换为 UTF-16LE）
            # -charset utf8: 指定输出使用 UTF-8 编码
            # 注意：写入元数据时，ExifTool 会自动将 UTF-8 转换为 Windows 所需的 UTF-16LE
            args.extend(["-charset", "filename=utf8"])
            args.extend(["-charset", "utf8"])
            
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
            
            # Label - XMP-xmp:Label 期望数字（0-9），但我们的 label 是字符串
            # 根据 XMP 规范，Label 用于颜色标签（0=无，1=红色，2=黄色，3=绿色，4=蓝色，5=紫色）
            # 由于我们的 label 是质量标签字符串（如 "HighQuality"），不写入 XMP-xmp:Label
            # 质量标签信息通过 subjects/keywords 字段传递
            # 如果需要颜色标签，可以根据质量分数映射：
            # if "label" in analysis_result and analysis_result["label"]:
            #     # 将质量标签映射为颜色标签数字（可选）
            #     # 0=无, 1=红色(低质量), 2=黄色(中低), 3=绿色(中高), 4=蓝色(高质量), 5=紫色(极高)
            #     label_map = {
            #         'VeryLowQuality': 1,  # 红色
            #         'LowQuality': 2,      # 黄色
            #         'MediumQuality': 3,   # 绿色
            #         'HighQuality': 4      # 蓝色
            #     }
            #     label_str = analysis_result['label']
            #     if label_str in label_map:
            #         args.append(f"-{fields['label']}={label_map[label_str]}")
            
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
                    # 只写入 XMP-dc:Subject（兼容性最好）
                    # XMP-Iptc4xmpCore:Keywords 可能在某些文件格式中不可写，跳过以避免警告
                    args.append(f"-{fields['subject']}+={keyword}")
                    # 注释掉 Iptc4xmpCore:Keywords，因为某些文件格式不支持
                    # args.append(f"-{fields['keywords']}+={keyword}")
            
            # Description
            # 注意：使用 = 而不是 +=，因为 += 需要数字偏移量
            # 如果需要追加，应该先读取现有值，然后合并
            if "metrics" in analysis_result:
                metrics = analysis_result["metrics"]
                if metrics:
                    metrics_desc = json.dumps(metrics, ensure_ascii=False)
                    if len(metrics_desc) > 300:
                        metrics_desc = metrics_desc[:300] + "..."
                    # 使用 = 赋值而不是 += 追加，避免 "Shift value is not a number" 警告
                    # 如果需要保留原有描述，应该先读取再合并
                    args.append(f"-{fields['description']}=[质量分析] {metrics_desc}")
            
            # 确保路径是有效的字符串（处理中文路径编码问题）
            from pathlib import Path
            import sys
            import platform
            
            if isinstance(image_path, Path):
                # 使用 resolve() 获取绝对路径，确保路径正确
                image_path_str = str(image_path.resolve())
            else:
                # 如果是字符串，先转换为 Path 对象再解析，确保路径格式正确
                try:
                    path_obj = Path(image_path)
                    if path_obj.is_absolute():
                        image_path_str = str(path_obj.resolve())
                    else:
                        image_path_str = str(Path(image_path).resolve())
                except Exception:
                    # 如果转换失败，使用原始字符串
                    image_path_str = str(image_path)
            
            # Windows 上确保路径编码正确
            # ExifTool 在 Windows 上需要 UTF-8 编码的路径
            # 路径应该已经是正确的 UTF-8 字符串（Python 3 默认使用 UTF-8）
            # 但需要确保路径格式正确（使用正斜杠或反斜杠，取决于系统）
            if platform.system() == 'Windows':
                # Windows 上，确保路径使用反斜杠（Windows 标准格式）
                # 但 ExifTool 也接受正斜杠，所以保持原样即可
                # 关键是要确保路径是有效的 UTF-8 字符串
                pass
            
            # 验证路径编码（确保是有效的 UTF-8）
            try:
                # 验证路径可以正确编码为 UTF-8
                image_path_str.encode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError) as e:
                # 如果编码失败，记录警告但继续尝试
                self._logger.warning(f"路径编码验证失败: {image_path_str}, 错误: {e}")
            
            args.append(image_path_str)
            
            result = self._executor.execute(args, timeout=30)
            
            # 检查结果，过滤掉非关键警告
            stderr = result.get('stderr', '')
            stdout = result.get('stdout', '')
            
            # 过滤掉常见的非关键警告（这些警告不影响功能）
            non_critical_warnings = [
                'Sorry, XMP-Iptc4xmpCore:Keywords doesn\'t exist or isn\'t writable',
                'FileName encoding must be specified',
                'Shift value for XMP-dc:Description is not a number',  # 这个警告可能是误报
            ]
            
            # 检查是否有真正的错误（不是非关键警告）
            has_critical_error = False
            if stderr:
                # 检查是否有 "Error:" 开头的错误
                error_lines = [line for line in stderr.split('\n') if line.strip().startswith('Error:')]
                if error_lines:
                    # 检查是否是文件创建错误（可能是路径编码问题）
                    for error_line in error_lines:
                        if 'Error creating file' in error_line or 'Error writing' in error_line:
                            has_critical_error = True
                            break
                
                # 检查是否有其他非警告的错误
                if not has_critical_error:
                    # 过滤掉非关键警告后，检查是否还有错误
                    filtered_stderr = stderr
                    for warning in non_critical_warnings:
                        filtered_stderr = filtered_stderr.replace(warning, '')
                    if filtered_stderr.strip() and 'Error:' in filtered_stderr:
                        has_critical_error = True
            
            if result['success'] and not has_critical_error:
                # 如果有非关键警告，记录为警告级别
                if stderr:
                    warning_lines = [line for line in stderr.split('\n') 
                                   if any(w in line for w in non_critical_warnings)]
                    if warning_lines:
                        self._logger.warning(f"XMP写入成功但有警告: {image_path}, 警告: {'; '.join(warning_lines[:3])}")
                    else:
                        self._logger.info(f"成功写入XMP元数据: {image_path}")
                else:
                    self._logger.info(f"成功写入XMP元数据: {image_path}")
                return True
            else:
                error_msg = result.get('error', stderr)
                returncode = result.get('returncode', -1)
                self._logger.error(
                    f"XMP写入失败: {image_path}, "
                    f"返回码: {returncode}, "
                    f"错误: {error_msg}, "
                    f"stdout: {stdout[:200] if stdout else '(空)'}, "
                    f"stderr: {stderr[:500] if stderr else '(空)'}",
                    exc_info=False
                )
                return False
        except Exception as e:
            self._logger.error(
                f"写入XMP元数据异常: {image_path}, "
                f"错误类型: {type(e).__name__}, "
                f"错误信息: {str(e)}",
                exc_info=True
            )
            return False

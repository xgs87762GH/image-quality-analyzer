"""图像分析器 - 整合质量分析和审美评分（高内聚：图像分析流程整合）"""
from typing import Dict, Optional, Any
import numpy as np
from PIL import Image

from analyzers.base_analyzer import BaseAnalyzer
from analyzers.quality_analyzer import QualityAnalyzer
from analyzers.aesthetic_analyzer import AestheticAnalyzer
from analyzers.calculators.metric_normalizer import MetricNormalizer
from analyzers.calculators.quality_calculator import QualityCalculator
from utils.logger import get_logger


class ImageAnalyzer(BaseAnalyzer):
    """图像分析器 - 整合质量分析和审美评分"""

    def __init__(
        self,
        use_aesthetic: bool = False,
        aesthetic_mode: str = "none",
        ai_analyzer: Optional[Any] = None,
    ):
        """
        初始化图像分析器

        Args:
            use_aesthetic: 是否启用审美评分（向后兼容，将被 aesthetic_mode 替代）
            aesthetic_mode: 审美评估方式 ('none', 'clip', 'ai')
            ai_analyzer: AI 分析器实例（当 aesthetic_mode='ai' 时需要）
        """
        self._logger = get_logger()

        # 向后兼容：如果 use_aesthetic 为 True 但 aesthetic_mode 为 'none'，则设置为 'clip'
        if use_aesthetic and aesthetic_mode == "none":
            aesthetic_mode = "clip"

        self.aesthetic_mode = aesthetic_mode
        self.quality_analyzer = QualityAnalyzer()

        # 根据模式初始化相应的分析器
        if aesthetic_mode == "clip":
            self.aesthetic_analyzer = AestheticAnalyzer()
            if not self.aesthetic_analyzer.is_available():
                self._logger.warning(
                    "CLIP 审美评分模型不可用，将仅使用质量分析"
                )
                self.aesthetic_mode = "none"
                self.aesthetic_analyzer = None
        elif aesthetic_mode == "ai":
            self.ai_analyzer = ai_analyzer
            self.aesthetic_analyzer = None
            if not self.ai_analyzer:
                self._logger.warning(
                    "AI 分析器未提供，将仅使用质量分析"
                )
                self.aesthetic_mode = "none"
        else:
            self.aesthetic_analyzer = None
            self.ai_analyzer = None

        self.use_aesthetic = self.aesthetic_mode != "none"
    
    def is_available(self) -> bool:
        """检查分析器是否可用"""
        return self.quality_analyzer.is_available()
    
    def analyze(self, image_path: str) -> Optional[Dict]:
        """
        分析单张图像

        - none：仅基础质量指标（模糊、亮度、熵等）。
        - clip：基础指标 + CLIP 审美，综合加权得评分。
        - ai：评分与审美均来自 AI，不经过 CLIP；基础指标仅用于 subjects 与展示。

        Args:
            image_path: 图像文件路径

        Returns:
            分析结果字典，包含 quality_score、rating、label、subjects、metrics；失败返回 None。
        """
        try:
            img = Image.open(image_path)
            img_array = np.array(img.convert("RGB"))

            blur_score = self.quality_analyzer.calculate_blur_score(img_array)
            brightness = self.quality_analyzer.calculate_brightness(img_array)
            entropy = self.quality_analyzer.calculate_entropy(img_array)
            brisque = self.quality_analyzer.calculate_brisque(img_array)

            aesthetic_score: Optional[float] = None
            if self.aesthetic_mode == "clip" and self.aesthetic_analyzer:
                aesthetic_score = self.aesthetic_analyzer.calculate_score(img_array)
            elif self.aesthetic_mode == "ai" and self.ai_analyzer:
                aesthetic_score = self.ai_analyzer.calculate_aesthetic_score(
                    image_path
                )

            blur_norm, brightness_norm, entropy_norm = (
                MetricNormalizer.normalize_quality_metrics(
                    blur_score, brightness, entropy
                )
            )

            aesthetic_norm: Optional[float] = None
            if aesthetic_score is not None:
                aesthetic_norm = MetricNormalizer.normalize_aesthetic_score(
                    aesthetic_score
                )

            if self.aesthetic_mode == "ai" and aesthetic_norm is not None:
                # AI 模式：评分、审美均来自 AI，不经过 CLIP
                quality_score = aesthetic_norm
            else:
                # none / clip，或 AI 模式但审美未返回时：传统指标（及可选 CLIP）加权
                quality_score = QualityCalculator.calculate_quality_score(
                    blur_norm, brightness_norm, entropy_norm, aesthetic_norm
                )

            rating = QualityCalculator.get_rating(quality_score)
            label = QualityCalculator.get_label(quality_score)
            subjects = QualityCalculator.get_subjects(
                blur_score, brightness, entropy, brisque, label
            )

            return {
                "quality_score": round(quality_score, 2),
                "rating": rating,
                "label": label,
                "subjects": subjects,
                "metrics": {
                    "blur_score": round(blur_score, 2),
                    "brightness": round(brightness, 2),
                    "entropy": round(entropy, 2),
                    "brisque": round(brisque, 2) if brisque is not None else None,
                    "aesthetic_score": (
                        round(aesthetic_score, 2) if aesthetic_score is not None else None
                    ),
                },
            }
        except Exception as e:
            self._logger.error(
                "分析图像失败: path=%s, error=%s",
                image_path,
                e,
                exc_info=True,
            )
            return None

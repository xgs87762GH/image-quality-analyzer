"""审美评分分析器（高内聚：CLIP审美评分逻辑集中）"""
from typing import Optional, Dict, Any
import numpy as np
from PIL import Image

from analyzers.base_analyzer import BaseAnalyzer

# 尝试导入可选依赖
try:
    import torch
    from transformers import CLIPProcessor, CLIPModel
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False
    torch = None
    CLIPProcessor = None
    CLIPModel = None


class AestheticAnalyzer(BaseAnalyzer):
    """审美评分分析器 - 基于CLIP模型"""
    
    def __init__(self):
        self.model = None
        self.processor = None
        self._load_model()
    
    def _load_model(self):
        """加载CLIP模型"""
        if not HAS_DEPENDENCIES:
            return
        
        try:
            print("正在加载审美评分模型...")
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            print("审美模型加载完成")
        except Exception as e:
            print(f"警告: 无法加载审美模型: {e}")
            self.model = None
            self.processor = None
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        return self.model is not None and self.processor is not None
    
    def analyze(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        分析图像（实现BaseAnalyzer接口）
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            分析结果字典，包含审美评分
        """
        try:
            from PIL import Image
            import numpy as np
            
            img = Image.open(image_path)
            img_array = np.array(img.convert('RGB'))
            score = self.calculate_score(img_array)
            
            if score is not None:
                return {'aesthetic_score': score}
            return None
        except Exception:
            return None
    
    def calculate_score(self, image: np.ndarray) -> Optional[float]:
        """
        计算审美评分
        
        Args:
            image: RGB图像数组
            
        Returns:
            审美评分（0-10），如果不可用则返回None
        """
        if not self.is_available():
            return None
        
        try:
            # 转换为PIL Image
            pil_image = Image.fromarray(image)
            
            # 定义文本提示
            positive_texts = [
                "a beautiful photo",
                "a high quality image",
                "an aesthetic photograph"
            ]
            negative_texts = [
                "a low quality image",
                "a blurry photo"
            ]
            all_texts = positive_texts + negative_texts
            
            # 处理输入
            inputs = self.processor(
                images=pil_image,
                text=all_texts,
                return_tensors="pt",
                padding=True
            )
            
            # 计算相似度
            with torch.no_grad():
                outputs = self.model(**inputs)
                image_features = outputs.image_embeds
                text_features = outputs.text_embeds
                
                # 计算与正面文本的平均相似度
                positive_similarities = torch.nn.functional.cosine_similarity(
                    image_features, text_features[:len(positive_texts)], dim=1
                )
                aesthetic_score = float(positive_similarities.mean().item() * 5 + 5)  # 映射到0-10
                return max(0, min(10, aesthetic_score))
        except Exception as e:
            print(f"审美评分计算错误: {e}")
            return None

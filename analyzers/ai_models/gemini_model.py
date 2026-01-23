"""Gemini模型实现（高内聚：Gemini相关逻辑集中）"""
from typing import Dict, Any
from pathlib import Path

from .base_model import BaseAIModel


class GeminiModel(BaseAIModel):
    """Gemini模型实现"""
    
    def __init__(self, api_key: str):
        """
        初始化Gemini模型
        
        Args:
            api_key: Google API密钥
        """
        self.api_key = api_key
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查依赖是否已安装"""
        try:
            import google.generativeai as genai
            self._genai = genai
        except ImportError:
            self._genai = None
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        return self._genai is not None and self.api_key is not None
    
    def analyze(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        使用Gemini分析图像
        
        Args:
            image_path: 图像文件路径
            prompt: 提示词
            
        Returns:
            分析结果
        """
        if not self.is_available():
            return {'success': False, 'error': 'google-generativeai库未安装或API密钥未设置'}
        
        if not Path(image_path).exists():
            return {'success': False, 'error': '图像文件不存在'}
        
        try:
            self._genai.configure(api_key=self.api_key)
            model = self._genai.GenerativeModel('gemini-pro-vision')
            
            default_prompt = """请分析这张图片，提供以下信息：
1. 图片质量评估（清晰度、色彩、构图等）
2. 主要内容描述
3. 可能的用途或场景
4. 改进建议（如果有）"""
            
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            response = model.generate_content([
                prompt or default_prompt,
                {"mime_type": "image/jpeg", "data": image_data}
            ])
            
            analysis_text = response.text
            
            return {
                'success': True,
                'model': 'gemini',
                'analysis': analysis_text,
                'raw_response': response.model_dump()
            }
        except ImportError:
            return {'success': False, 'error': 'google-generativeai库未安装，请运行: pip install google-generativeai'}
        except Exception as e:
            return {'success': False, 'error': f'Gemini分析失败: {str(e)}'}

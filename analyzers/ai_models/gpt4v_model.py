"""GPT-4 Vision模型实现（高内聚：GPT-4V相关逻辑集中）"""
import base64
from typing import Dict, Any, Optional
from pathlib import Path

from .base_model import BaseAIModel


class GPT4VModel(BaseAIModel):
    """GPT-4 Vision模型实现"""
    
    def __init__(self, api_key: str):
        """
        初始化GPT-4 Vision模型
        
        Args:
            api_key: OpenAI API密钥
        """
        self.api_key = api_key
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查依赖是否已安装"""
        try:
            import openai
            self._openai = openai
        except ImportError:
            self._openai = None
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        return self._openai is not None and self.api_key is not None
    
    def analyze(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        使用GPT-4 Vision分析图像
        
        Args:
            image_path: 图像文件路径
            prompt: 提示词
            
        Returns:
            分析结果
        """
        if not self.is_available():
            return {'success': False, 'error': 'openai库未安装或API密钥未设置'}
        
        if not Path(image_path).exists():
            return {'success': False, 'error': '图像文件不存在'}
        
        try:
            # 读取图像并编码为base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # 确定图像格式
            ext = Path(image_path).suffix.lower()
            mime_type = f"image/{ext[1:]}" if ext else "image/jpeg"
            
            default_prompt = """请分析这张图片，提供以下信息：
1. 图片质量评估（清晰度、色彩、构图等）
2. 主要内容描述
3. 可能的用途或场景
4. 改进建议（如果有）"""
            
            client = self._openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt or default_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            analysis_text = response.choices[0].message.content
            
            return {
                'success': True,
                'model': 'gpt4v',
                'analysis': analysis_text,
                'raw_response': response.model_dump()
            }
        except ImportError:
            return {'success': False, 'error': 'openai库未安装，请运行: pip install openai'}
        except Exception as e:
            return {'success': False, 'error': f'GPT-4 Vision分析失败: {str(e)}'}

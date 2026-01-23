"""Claude模型实现（高内聚：Claude相关逻辑集中）"""
import base64
from typing import Dict, Any
from pathlib import Path

from .base_model import BaseAIModel


class ClaudeModel(BaseAIModel):
    """Claude模型实现"""
    
    def __init__(self, api_key: str):
        """
        初始化Claude模型
        
        Args:
            api_key: Anthropic API密钥
        """
        self.api_key = api_key
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查依赖是否已安装"""
        try:
            import anthropic
            self._anthropic = anthropic
        except ImportError:
            self._anthropic = None
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        return self._anthropic is not None and self.api_key is not None
    
    def analyze(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        使用Claude分析图像
        
        Args:
            image_path: 图像文件路径
            prompt: 提示词
            
        Returns:
            分析结果
        """
        if not self.is_available():
            return {'success': False, 'error': 'anthropic库未安装或API密钥未设置'}
        
        if not Path(image_path).exists():
            return {'success': False, 'error': '图像文件不存在'}
        
        try:
            # 读取图像
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            default_prompt = """请分析这张图片，提供以下信息：
1. 图片质量评估（清晰度、色彩、构图等）
2. 主要内容描述
3. 可能的用途或场景
4. 改进建议（如果有）"""
            
            client = self._anthropic.Anthropic(api_key=self.api_key)
            message = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": base64.b64encode(image_data).decode('utf-8')
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt or default_prompt
                            }
                        ]
                    }
                ]
            )
            
            analysis_text = message.content[0].text
            
            return {
                'success': True,
                'model': 'claude',
                'analysis': analysis_text,
                'raw_response': message.model_dump()
            }
        except ImportError:
            return {'success': False, 'error': 'anthropic库未安装，请运行: pip install anthropic'}
        except Exception as e:
            return {'success': False, 'error': f'Claude分析失败: {str(e)}'}

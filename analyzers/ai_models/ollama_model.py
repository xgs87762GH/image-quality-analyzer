"""Ollama模型实现（高内聚：Ollama相关逻辑集中）"""
import base64
import json
import time
import requests
from typing import Dict, Any
from pathlib import Path

from .base_model import BaseAIModel
from utils.logger import get_logger


class OllamaModel(BaseAIModel):
    """Ollama模型实现"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        """
        初始化Ollama模型
        
        Args:
            base_url: Ollama API地址
            model: Ollama模型名称
        """
        self.base_url = base_url
        self.model = model
        self.logger = get_logger()
    
    def is_available(self) -> bool:
        """检查模型是否可用（通过检查服务是否可访问）"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def analyze(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        使用Ollama分析图像
        
        Args:
            image_path: 图像文件路径
            prompt: 提示词
            
        Returns:
            分析结果
        """
        if not Path(image_path).exists():
            return {
                'success': False,
                'error': f'图像文件不存在: {image_path}'
            }
        
        try:
            # 读取图像并编码为base64
            try:
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                    image_data = base64.b64encode(image_bytes).decode('utf-8')
            except Exception as e:
                self.logger.error(f"读取图像文件失败: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': f'读取图像文件失败: {str(e)}'
                }
            
            default_prompt = """请分析这张图片，提供以下信息：
1. 图片质量评估（清晰度、色彩、构图等）
2. 主要内容描述
3. 可能的用途或场景
4. 改进建议（如果有）

请用中文回答。"""
            
            # 检查是否是视觉模型
            is_vision_model = self._is_vision_model(self.model)
            
            # 构建请求数据
            request_data = {
                "model": self.model,
                "prompt": prompt or default_prompt,
                "stream": False
            }
            
            if is_vision_model:
                request_data["images"] = [image_data]
                self.logger.info(f"使用视觉模型 {self.model} 分析图像: {image_path}")
            else:
                self.logger.warning(f"模型 {self.model} 不是视觉模型，将只发送文本提示（无法分析图像内容）")
            
            # 发送请求
            api_url = f"{self.base_url}/api/generate"
            self.logger.info(f"[Ollama] 请求配置: URL={api_url}, 模型={self.model}, 视觉模型={'是' if is_vision_model else '否'}")
            
            request_start = time.time()
            self.logger.info(f"[Ollama] 发送请求... (超时: 300秒)")
            
            response = requests.post(
                api_url,
                json=request_data,
                timeout=300,
                stream=False
            )
            request_duration = time.time() - request_start
            
            self.logger.info(f"[Ollama] 请求完成: 状态码={response.status_code}, 耗时={request_duration:.2f}秒")
            
            if response.status_code != 200:
                error_text = response.text[:500] if response.text else "无错误信息"
                self.logger.error(f"[Ollama] API错误: 状态码={response.status_code}, 错误信息={error_text}")
                return {
                    'success': False,
                    'error': f'Ollama API错误: {response.status_code} - {error_text}'
                }
            
            try:
                result = response.json()
                analysis_text = result.get('response', '')
                
                if 'error' in result:
                    error_msg = result.get('error', '未知错误')
                    self.logger.error(f"Ollama返回错误: {error_msg}")
                    return {
                        'success': False,
                        'error': f'Ollama错误: {error_msg}'
                    }
                
                self.logger.info(f"[Ollama] ✓ 分析成功: 响应长度={len(analysis_text):,} 字符")
                
                return {
                    'success': True,
                    'model': f'ollama-{self.model}',
                    'analysis': analysis_text,
                    'raw_response': result
                }
            except json.JSONDecodeError as e:
                error_preview = response.text[:500] if response.text else "无响应内容"
                self.logger.error(f"解析Ollama响应失败: {e}, 响应内容: {error_preview}")
                return {
                    'success': False,
                    'error': f'解析Ollama响应失败: {str(e)}'
                }
                
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"无法连接到Ollama服务 ({self.base_url}): {e}", exc_info=True)
            return {
                'success': False,
                'error': f'无法连接到Ollama服务 ({self.base_url})，请确保Ollama正在运行'
            }
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Ollama请求超时: {e}", exc_info=True)
            return {
                'success': False,
                'error': 'Ollama请求超时，请检查模型是否已下载'
            }
        except Exception as e:
            self.logger.error(f"Ollama分析失败 (模型: {self.model}, URL: {self.base_url}): {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Ollama分析失败: {str(e)}'
            }
    
    @staticmethod
    def _is_vision_model(model_name: str) -> bool:
        """
        检查模型是否是视觉模型（支持图像输入）
        
        Args:
            model_name: 模型名称
            
        Returns:
            如果是视觉模型返回True
        """
        model_lower = model_name.lower()
        vision_keywords = [
            "llava", "vision", "bakllava", "qwen3vl", "qwen3-vl",
            "qwen-vl", "qwen2-vl", "moondream", "minicpm-v"
        ]
        return any(keyword in model_lower for keyword in vision_keywords)
    
    def get_models(self) -> Dict[str, Any]:
        """
        获取Ollama可用模型列表
        
        Returns:
            模型列表
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'无法获取模型列表: {response.status_code}'
                }
            
            result = response.json()
            models = [model['name'] for model in result.get('models', [])]
            
            return {
                'success': True,
                'models': models
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': f'无法连接到Ollama服务 ({self.base_url})'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

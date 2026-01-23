"""模型管理服务"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess

from utils.logger import get_logger


class ModelService:
    """模型管理服务"""
    
    def __init__(self):
        self.logger = get_logger()
    
    def download_aesthetic_model(self, model_name: str = "openai/clip-vit-base-patch32") -> Dict[str, Any]:
        """
        下载审美评分模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            下载结果
        """
        try:
            from transformers import CLIPProcessor, CLIPModel
            
            self.logger.info(f"开始下载模型: {model_name}")
            
            # 下载模型（会自动缓存）
            processor = CLIPProcessor.from_pretrained(model_name)
            model = CLIPModel.from_pretrained(model_name)
            
            # 获取模型路径
            cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
            model_path = cache_dir / f"models--{model_name.replace('/', '--')}"
            
            # 计算模型大小
            total_size = 0
            if model_path.exists():
                for file_path in model_path.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            
            self.logger.info(f"模型下载完成: {model_name}")
            
            return {
                'success': True,
                'model_name': model_name,
                'model_path': str(model_path),
                'size': f"{total_size / 1024**2:.2f} MB",
                'message': '模型下载成功'
            }
        except ImportError:
            return {
                'success': False,
                'error': 'transformers库未安装，请运行: pip install transformers torch'
            }
        except Exception as e:
            self.logger.error(f"模型下载失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_model_status(self, model_name: str = "openai/clip-vit-base-patch32") -> Dict[str, Any]:
        """检查模型状态"""
        try:
            from transformers import CLIPProcessor, CLIPModel
            from pathlib import Path
            
            cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
            model_path = cache_dir / f"models--{model_name.replace('/', '--')}"
            
            downloaded = model_path.exists()
            
            size = None
            if downloaded:
                total_size = 0
                for file_path in model_path.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                size = f"{total_size / 1024**2:.2f} MB"
            
            return {
                'downloaded': downloaded,
                'model_name': model_name,
                'model_path': str(model_path) if downloaded else None,
                'size': size
            }
        except ImportError:
            return {
                'downloaded': False,
                'error': 'transformers库未安装'
            }
        except Exception as e:
            return {
                'downloaded': False,
                'error': str(e)
            }

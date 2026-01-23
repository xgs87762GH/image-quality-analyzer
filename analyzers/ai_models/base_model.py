"""AI模型基类（低耦合：定义统一接口）"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAIModel(ABC):
    """AI模型基类 - 所有AI模型实现都应继承此类"""
    
    @abstractmethod
    def analyze(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        使用AI模型分析图像
        
        Args:
            image_path: 图像文件路径
            prompt: 提示词
            
        Returns:
            分析结果，包含：
            - success: 是否成功
            - analysis: 分析文本
            - error: 错误信息（如果失败）
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查模型是否可用（依赖是否已安装）
        
        Returns:
            如果可用返回True，否则返回False
        """
        pass

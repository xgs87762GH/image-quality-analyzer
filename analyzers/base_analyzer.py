"""分析器基类 - 定义分析器的通用接口（低耦合：统一接口）"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class BaseAnalyzer(ABC):
    """分析器基类 - 所有分析器都应继承此类（高内聚：统一接口定义）"""
    
    @abstractmethod
    def analyze(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        分析图像
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            分析结果字典，如果失败则返回None
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查分析器是否可用（依赖是否已安装）
        
        Returns:
            如果可用返回True，否则返回False
        """
        pass

"""服务工厂 - 统一管理服务实例的创建（单例模式）"""
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from services.image_service import ImageService
    from services.quality_service import QualityService
    from services.auto_import_service import AutoImportService
    from analyzers.ai_analyzer import AIAnalyzer


class ServiceFactory:
    """服务工厂 - 提供统一的服务实例创建接口"""
    
    _image_service: Optional['ImageService'] = None
    _quality_service: Optional['QualityService'] = None
    _auto_import_service: Optional['AutoImportService'] = None
    
    @classmethod
    def get_image_service(cls, **kwargs) -> 'ImageService':
        """
        获取图像服务实例（单例）
        
        Args:
            **kwargs: 传递给ImageService的初始化参数
            
        Returns:
            ImageService实例
        """
        if cls._image_service is None or kwargs:
            from services.image_service import ImageService
            cls._image_service = ImageService(**kwargs)
        return cls._image_service
    
    @classmethod
    def get_quality_service(cls) -> 'QualityService':
        """
        获取质量服务实例（单例）
        
        Returns:
            QualityService实例
        """
        if cls._quality_service is None:
            from services.quality_service import QualityService
            cls._quality_service = QualityService()
        return cls._quality_service
    
    @classmethod
    def get_auto_import_service(cls) -> 'AutoImportService':
        """
        获取自动导入服务实例（单例）
        
        Returns:
            AutoImportService实例
        """
        if cls._auto_import_service is None:
            from services.auto_import_service import AutoImportService
            cls._auto_import_service = AutoImportService()
        return cls._auto_import_service
    
    @classmethod
    def create_ai_analyzer(cls, model: str = "gpt4v", api_key: Optional[str] = None,
                          ollama_base_url: Optional[str] = None,
                          ollama_model: Optional[str] = None) -> 'AIAnalyzer':
        """
        创建AI分析器实例（每次创建新实例）
        
        Args:
            model: 模型名称
            api_key: API密钥
            ollama_base_url: Ollama API地址
            ollama_model: Ollama模型名称
            
        Returns:
            AIAnalyzer实例
        """
        from analyzers.ai_analyzer import AIAnalyzer
        return AIAnalyzer(
            model=model,
            api_key=api_key,
            ollama_base_url=ollama_base_url,
            ollama_model=ollama_model
        )
    
    @classmethod
    def reset(cls):
        """重置所有服务实例（主要用于测试）"""
        cls._image_service = None
        cls._quality_service = None
        cls._auto_import_service = None

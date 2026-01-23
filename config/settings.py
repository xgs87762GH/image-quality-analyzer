"""配置管理"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """数据库配置"""
    db_path: str = "data/image_quality.db"
    pool_size: int = 5
    timeout: float = 20.0
    check_same_thread: bool = False


@dataclass
class AnalyzerConfig:
    """分析器配置"""
    use_aesthetic: bool = False
    blur_weight: float = 0.4
    brightness_weight: float = 0.3
    entropy_weight: float = 0.3
    aesthetic_weight: float = 0.3


@dataclass
class MetadataConfig:
    """元数据配置"""
    exiftool_path: str = "exiftool"
    write_to_xmp: bool = True
    backup_original: bool = True


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    log_dir: str = "logs"
    log_file: str = "image_quality.log"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class TrashConfig:
    """回收站配置"""
    trash_dir: str = "trash"
    preserve_structure: bool = True  # 保留原目录结构


@dataclass
class Settings:
    """应用配置"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    analyzer: AnalyzerConfig = field(default_factory=AnalyzerConfig)
    metadata: MetadataConfig = field(default_factory=MetadataConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    trash: TrashConfig = field(default_factory=TrashConfig)
    
    # 图像扩展名
    image_extensions: list = field(default_factory=lambda: [
        '.jpg', '.jpeg', '.png', '.webp', '.tiff', '.tif'
    ])
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保目录存在
        db_dir = Path(self.database.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        log_dir = Path(self.logging.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        trash_dir = Path(self.trash.trash_dir)
        trash_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_env(cls) -> 'Settings':
        """从环境变量加载配置"""
        settings = cls()
        
        # 数据库配置
        if db_path := os.getenv('DB_PATH'):
            settings.database.db_path = db_path
        
        # 分析器配置
        if use_aesthetic := os.getenv('USE_AESTHETIC'):
            settings.analyzer.use_aesthetic = use_aesthetic.lower() == 'true'
        
        # 元数据配置
        if exiftool_path := os.getenv('EXIFTOOL_PATH'):
            settings.metadata.exiftool_path = exiftool_path
        
        # 日志配置
        if log_level := os.getenv('LOG_LEVEL'):
            settings.logging.level = log_level
        
        return settings


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局配置实例"""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


def set_settings(settings: Settings):
    """设置全局配置实例"""
    global _settings
    _settings = settings

"""配置管理"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """数据库配置"""
    # 默认使用 AppData 目录下的数据库，避免 E: 盘文件系统问题和权限问题
    # 数据库会保存在 C:\Users\用户名\AppData\Local\ImageQualityAnalyzer\data\image_quality.db
    db_path: str = field(default_factory=lambda: str(Path.home() / "AppData" / "Local" / "ImageQualityAnalyzer" / "data" / "image_quality.db"))
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
    exiftool_path: str = "exiftool"  # 默认使用系统PATH，会自动检测项目内的ExifTool
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


def _get_default_trash_dir() -> str:
    """
    获取默认回收站目录路径
    
    默认：用户目录/ImageQualityAnalyzer/Trash
    例如：C:/Users/用户名/ImageQualityAnalyzer/Trash
    
    Returns:
        回收站目录路径（字符串）
    """
    # 获取用户主目录
    user_home = Path.home()
    
    # 项目名称（规范命名）
    project_name = "ImageQualityAnalyzer"
    trash_folder_name = "Trash"
    
    # 构建默认路径
    default_path = user_home / project_name / trash_folder_name
    
    # 确保目录存在
    default_path.mkdir(parents=True, exist_ok=True)
    
    return str(default_path.absolute())


@dataclass
class TrashConfig:
    """
    回收站配置
    
    默认路径：用户目录下的 ImageQualityAnalyzer/Trash
    可以通过环境变量 TRASH_DIR 自定义
    """
    trash_dir: str = "trash"  # 默认值，在 Settings.__post_init__ 中会被替换为默认路径
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
        """
        初始化后处理
        
        确保所有必要的目录存在：
        - 数据库目录
        - 日志目录
        - 回收站目录（如果不存在则创建）
        
        注意：此方法在日志系统初始化之前调用，不能使用 get_logger()
        """
        # 确保数据库目录存在（带错误处理）
        db_dir = Path(self.database.db_path).parent
        try:
            db_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            # 如果创建失败，尝试使用临时目录
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "ImageQualityAnalyzer" / "data"
            try:
                temp_dir.mkdir(parents=True, exist_ok=True)
                self.database.db_path = str(temp_dir / "image_quality.db")
                print(f"警告: 无法在 {db_dir} 创建数据库目录，使用临时目录: {self.database.db_path}")
            except Exception as e2:
                # 如果临时目录也失败，使用项目目录（即使可能有问题）
                fallback_dir = Path("data")
                fallback_dir.mkdir(parents=True, exist_ok=True)
                self.database.db_path = str(fallback_dir / "image_quality.db")
                print(f"警告: 无法创建数据库目录，使用项目目录: {self.database.db_path}")
        
        # 确保日志目录存在
        log_dir = Path(self.logging.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 确保回收站目录存在（如果不存在则创建）
        # 如果使用默认值 "trash"，则替换为用户目录下的默认路径
        if self.trash.trash_dir == "trash":
            try:
                self.trash.trash_dir = _get_default_trash_dir()
            except Exception:
                # 如果获取失败，保持使用项目目录下的 trash
                pass
        
        trash_dir = Path(self.trash.trash_dir)
        try:
            trash_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # 如果创建失败，使用项目目录下的trash作为降级方案
            fallback_trash_dir = Path("trash")
            fallback_trash_dir.mkdir(parents=True, exist_ok=True)
            self.trash.trash_dir = str(fallback_trash_dir.absolute())
    
    @classmethod
    def from_env(cls) -> 'Settings':
        """
        从环境变量加载配置
        
        支持的环境变量：
        - DB_PATH: 数据库路径
        - USE_AESTHETIC: 是否使用美学分析
        - EXIFTOOL_PATH: ExifTool路径
        - LOG_LEVEL: 日志级别
        - TRASH_DIR: 回收站目录路径（自定义）
        """
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
        
        # 回收站配置（支持自定义路径）
        if trash_dir := os.getenv('TRASH_DIR'):
            # 使用环境变量指定的路径
            custom_trash_dir = Path(trash_dir)
            # 确保目录存在
            custom_trash_dir.mkdir(parents=True, exist_ok=True)
            settings.trash.trash_dir = str(custom_trash_dir.absolute())
        
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

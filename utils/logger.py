"""日志系统"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from config.settings import get_settings


def setup_logger(name: str = "image_quality", log_file: Optional[str] = None) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径，如果为None则使用配置中的路径
        
    Returns:
        配置好的日志记录器
    """
    settings = get_settings()
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.logging.level))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果指定了日志文件）
    if log_file or settings.logging.log_file:
        log_path = Path(log_file or settings.logging.log_dir) / (settings.logging.log_file or "image_quality.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用UTF-8-sig编码（带BOM），Windows记事本可以正确识别
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=settings.logging.max_bytes,
            backupCount=settings.logging.backup_count,
            encoding='utf-8-sig'  # 使用UTF-8 with BOM（Windows兼容性更好）
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "image_quality") -> logging.Logger:
    """获取日志记录器"""
    logger = logging.getLogger(name)
    # 如果logger还没有处理器，设置它
    if not logger.handlers:
        setup_logger(name)
    return logger

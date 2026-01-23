"""常量定义"""

# 支持的图像格式
DEFAULT_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.tiff', '.tif']

# 质量分数阈值
QUALITY_THRESHOLDS = {
    'HIGH': 80,
    'MEDIUM': 60,
    'LOW': 40
}

# 质量标签
QUALITY_LABELS = {
    'HIGH': 'HighQuality',
    'MEDIUM': 'MediumQuality',
    'LOW': 'LowQuality',
    'VERY_LOW': 'VeryLowQuality'
}

# 质量指标权重
QUALITY_WEIGHTS = {
    'blur': 0.4,
    'brightness': 0.3,
    'entropy': 0.3,
    'aesthetic': 0.3  # 当启用审美评分时使用
}

# 归一化参数
NORMALIZATION_PARAMS = {
    'blur_threshold': 500,  # 模糊度阈值（Laplacian方差）
    'brightness_ideal': 150,  # 理想亮度值
    'brightness_tolerance': 1.5,  # 亮度容差
    'entropy_threshold': 7.0,  # 信息熵阈值
    'aesthetic_max': 10.0  # 审美评分最大值
}

# 问题检测阈值
ISSUE_THRESHOLDS = {
    'blur': 100,  # 模糊度阈值
    'brightness_low': 50,  # 过暗阈值
    'brightness_high': 200,  # 过亮阈值
    'entropy_low': 5,  # 低信息量阈值
    'brisque_high': 50  # BRISQUE高失真阈值
}

# XMP字段名称
XMP_FIELDS = {
    'rating': 'XMP-xmp:Rating',
    'label': 'XMP-xmp:Label',
    'subject': 'XMP-dc:Subject',
    'description': 'XMP-dc:Description'
}

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

# XMP字段名称（标准XMP标签，兼容主流图像管理软件）
XMP_FIELDS = {
    # XMP Core标签（最常用，兼容性最好）
    'rating': 'XMP-xmp:Rating',           # 星级评分 (1-5)
    'label': 'XMP-xmp:Label',             # 颜色标签
    'metadata_date': 'XMP-xmp:MetadataDate',  # 元数据修改日期
    
    # Dublin Core标签（标准元数据）
    'title': 'XMP-dc:Title',              # 标题
    'creator': 'XMP-dc:Creator',          # 作者/创作者
    'description': 'XMP-dc:Description',  # 描述
    'subject': 'XMP-dc:Subject',         # 主题/关键词
    'rights': 'XMP-dc:Rights',           # 版权信息
    
    # IPTC Core标签（新闻摄影常用）
    'headline': 'XMP-Iptc4xmpCore:Headline',  # 标题
    'keywords': 'XMP-Iptc4xmpCore:Keywords', # 关键词（数组）
}

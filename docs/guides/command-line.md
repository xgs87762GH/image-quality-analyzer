# 命令行使用指南

本文档说明如何使用命令行工具进行图像分析和查询。

## 基本命令

### 批量分析图像

```bash
# 分析单个目录
python -m cli.main -i "图片目录路径"

# 分析多个目录
python -m cli.main -i "目录1" "目录2" "目录3"

# 包含审美评分
python -m cli.main -i "图片目录" --aesthetic

# 指定输出CSV报告
python -m cli.main -i "图片目录" -o report.csv
```

### 查询数据库

```bash
# 查看统计信息
python -m cli.query --stats

# 查询指定评级的图像
python -m cli.query --rating 5  # 查询5星图像
python -m cli.query --rating-min 4 --rating-max 5  # 查询4-5星

# 查询指定标签的图像
python -m cli.query --label HighQuality
python -m cli.query --label LowQuality VeryLowQuality

# 查询质量分数范围
python -m cli.query --quality-min 80 --quality-max 100

# 查找重复图像
python -m cli.query --duplicates

# 导出查询结果
python -m cli.query --label LowQuality --output results.json
```

### 按元数据筛选

```bash
# 列出所有图像的元数据
python -m cli.filter -i "图片目录" --list

# 查找低评级图像
python -m cli.filter -i "图片目录" --max-rating 2

# 查找低质量标签的图像
python -m cli.filter -i "图片目录" --label LowQuality VeryLowQuality

# 查找包含特定关键词的图像
python -m cli.filter -i "图片目录" --subject blurry

# 删除低质量图像（危险操作！）
python -m cli.filter -i "图片目录" --max-rating 2 --delete
```

## 命令行参数

### cli.main (批量分析)

```
-i, --input-dirs     输入目录（可多个）
-o, --output         输出CSV文件路径（可选）
--aesthetic          启用审美评分
--extensions         指定图像格式（默认：.jpg .jpeg .png .webp .tiff .bmp）
```

### cli.query (数据库查询)

```
--stats              显示统计信息
--rating             指定评级（1-5）
--rating-min         最小评级
--rating-max         最大评级
--label              指定标签
--quality-min        最小质量分数
--quality-max        最大质量分数
--duplicates         查找重复图像
--output             导出结果到JSON文件
```

### cli.filter (元数据筛选)

```
-i, --input-dir      输入目录
--list               列出所有元数据
--max-rating         最大评级
--min-rating         最小评级
--label              指定标签（可多个）
--subject            包含关键词
--delete             删除匹配的图像（危险！）
```

## 使用示例

### 示例1: 分析照片库

```bash
# 分析整个照片目录
python -m cli.main -i "F:\照片" -o photo_quality_report.csv

# 查看统计信息
python -m cli.query --stats

# 找出低质量照片
python -m cli.query --rating-max 2 --output low_quality.json
```

### 示例2: 批量处理多个目录

```bash
# 同时分析多个目录
python -m cli.main -i "D:\照片\2024" "D:\照片\2023" "E:\备份照片"
```

### 示例3: 查找和删除低质量图像

```bash
# 1. 先查找，不删除
python -m cli.filter -i "图片目录" --max-rating 2 -o low_quality_list.csv

# 2. 检查low_quality_list.csv，确认要删除的文件

# 3. 确认后删除
python -m cli.filter -i "图片目录" --max-rating 2 --delete
```

### 示例4: 查找重复图像

```bash
# 查找所有重复图像
python -m cli.query --duplicates --output duplicates.json

# 查看结果
cat duplicates.json
```

## 性能优化

### 大量图像处理

- 使用 `--extensions` 限制格式，减少处理时间
- 关闭审美评分（不使用 `--aesthetic`）
- 分批处理不同目录

### 查询优化

- 使用具体的查询条件（评级、标签）而不是范围查询
- 导出结果到文件而不是直接打印

## 输出格式

### CSV报告格式

```csv
file_path,quality_score,rating,label,blur_score,brightness,entropy
/path/to/image1.jpg,85.5,5,HighQuality,120.5,150.2,7.8
/path/to/image2.jpg,45.2,2,LowQuality,50.1,80.5,4.2
```

### JSON查询结果格式

```json
{
  "total": 100,
  "images": [
    {
      "id": 1,
      "file_path": "/path/to/image.jpg",
      "quality_score": 85.5,
      "rating": 5,
      "label": "HighQuality"
    }
  ]
}
```

## 故障排除

### 问题：处理很慢

**解决方案**:
- 关闭审美评分
- 限制图像格式
- 减少并发数量

### 问题：内存不足

**解决方案**:
- 分批处理
- 关闭审美评分
- 增加系统内存

### 问题：查询结果为空

**解决方案**:
- 确认数据库中有数据
- 检查查询条件是否正确
- 查看数据库文件是否存在

## 与Web界面配合使用

命令行工具和Web界面使用同一个数据库，可以：

1. 使用命令行批量分析大量图像
2. 使用Web界面查看和筛选结果
3. 使用命令行导出数据进行分析

## 更多信息

- [快速开始指南](../getting-started/README.md)
- [功能说明](../features/README.md)
- [Web界面使用指南](./web-interface.md)

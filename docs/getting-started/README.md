# 快速开始指南

欢迎使用 **Image Quality Analyzer (图像质量分析器)**！本指南将帮助您快速上手。

## 📋 目录

- [安装与配置](#安装与配置)
- [快速启动](#快速启动)
- [基本使用](#基本使用)
- [常见问题](#常见问题)

## 安装与配置

### 系统要求

- Python 3.10 或更高版本
- Windows / macOS / Linux
- 至少 2GB 可用内存
- 可选：GPU（用于CLIP模型审美评分）

### 1. 安装依赖

```bash
# 安装Python包
pip install -r requirements.txt

# 安装exiftool（必需，用于XMP元数据）
# Windows: 下载 https://exiftool.org/ 并添加到PATH
# macOS: brew install exiftool
# Ubuntu: sudo apt-get install libimage-exiftool-perl
```

### 2. 初始化数据库

```bash
# 首次使用需要初始化数据库
python scripts/init_database.py
```

### 3. 配置设置（可选）

编辑 `config/settings.py` 或通过Web界面设置：

- 数据库路径
- 是否启用审美评分
- XMP元数据写入选项

### 4. 验证安装

```bash
# 检查Python版本
python --version

# 检查依赖
python -c "import cv2, PIL, numpy, flask; print('✓ 所有依赖已安装')"

# 检查数据库
python -c "from database.connection import get_db; db = get_db(); print('✓ 数据库连接正常')"
```

## 快速启动

### 方式1: 直接启动（推荐）

```powershell
# 1. 激活conda环境
conda activate image_quality

# 2. 启动Web服务
python scripts/run_web.py
```

然后在浏览器中访问：**http://localhost:5000**

### 方式2: 使用启动脚本（自动处理环境）

**Windows批处理:**
```cmd
start.bat
```

**PowerShell:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_project.ps1
```

**详细启动说明**: 查看 [启动指南](./STARTUP_GUIDE.md)

#### 命令行批量处理

```bash
# 处理单个目录
python -m cli.main -i "图片目录路径"

# 处理多个目录
python -m cli.main -i "目录1" "目录2" "目录3"
```

## 基本使用

### Web界面使用

1. **启动Web服务**

   ```bash
   python scripts/run_web.py
   ```
2. **访问界面**

   - 打开浏览器访问 http://localhost:5000
   - 首次使用需要配置图片源目录（在设置中）
3. **导入图片**

   - 系统会自动从配置的目录导入图片
   - 或手动点击"批量导入"
4. **分析图片**

   - 选择要分析的图片
   - 点击"分析选中图片"
   - 等待分析完成
5. **查看结果**

   - 在图片列表中查看质量评分
   - 点击图片查看详细信息
   - 使用筛选功能查找特定质量的图片

### 命令行使用

```bash
# 批量分析图片
python -m cli.main -i "图片目录"

# 查询图片
python -m cli.query --rating 5  # 查询5星图片
python -m cli.query --label "High"  # 查询高质量图片

# 按元数据筛选
python -m cli.filter --rating 4 --output "高质量图片"
```

## 常见问题

### Q: 数据库初始化失败？

**A:** 确保有写入权限，检查 `data/` 目录是否存在。

### Q: Web界面无法访问？

**A:**

- 检查端口5000是否被占用
- 确认防火墙设置
- 查看日志文件 `logs/image_quality.log`

### Q: 图片分析很慢？

**A:**

- 关闭审美评分功能（在设置中）
- 减少并发分析数量
- 使用GPU加速（如果可用）

### Q: 如何配置AI模型？

**A:** 查看 [AI模型配置指南](../guides/ai-models.md)

### Q: 端口5000权限错误？

**A:** 这是Windows系统对端口的访问限制，解决方法：
1. **以管理员权限运行PowerShell**（推荐）
   - 右键点击PowerShell → 以管理员身份运行
   - 然后运行启动命令
2. **检查端口占用**
   ```powershell
   netstat -ano | findstr :5000
   # 如果被占用，结束进程：taskkill /PID XXXX /F
   ```
3. **检查防火墙设置**
   - 确保防火墙允许Python访问网络

详细说明查看 [启动指南](./STARTUP_GUIDE.md)

## 启动文件说明

项目中的启动相关文件：

- **`scripts/run_web.py`** ⭐ - 启动Web界面（端口5000）
- **`start.bat`** 🪟 - Windows批处理一键启动
- **`scripts/start_project.ps1`** 💻 - PowerShell一键启动
- **`main.py`** - 命令行工具入口（不是启动Web界面）

**详细说明**: 查看 [启动指南](./STARTUP_GUIDE.md)

## 下一步

- 📖 查看 [功能说明](../features/README.md) 了解所有功能
- 🏗️ 查看 [架构文档](../architecture/README.md) 了解项目结构
- 🔧 查看 [开发指南](../development/README.md) 参与开发

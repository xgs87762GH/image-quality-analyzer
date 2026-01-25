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

# ExifTool（自动下载，无需手动安装）
# 系统会在首次启动时自动下载ExifTool到项目目录，无需手动操作！
# 
# 如果自动下载失败，可以手动安装：
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

项目为前后端分离：后端 API（含 WebSocket）运行在 5000 端口，前端 React 应用运行在 5173 端口。**需同时启动两者**才能使用 Web 界面。

### 1. 启动后端 API

```powershell
conda activate image_quality   # 或你的虚拟环境
python scripts/run_web.py
```

后端地址：**http://localhost:5000**（仅 API，浏览器不直接访问）

### 2. 启动前端应用

```powershell
cd app
npm install   # 首次需安装依赖
npm run dev
```

然后在浏览器中访问：**http://localhost:5173**

### 使用启动脚本（可选）

**Windows 批处理:** `start.bat`  
**PowerShell:** `powershell -ExecutionPolicy Bypass -File scripts/start_project.ps1`

详见 [启动指南](./STARTUP_GUIDE.md)。

#### 命令行批量处理

```bash
# 处理单个目录
python -m cli.main -i "图片目录路径"

# 处理多个目录
python -m cli.main -i "目录1" "目录2" "目录3"
```

## 基本使用

### Web 界面使用

1. **启动后端与前端**（见上方「快速启动」）
2. **访问界面**：打开浏览器访问 http://localhost:5173
3. **配置**：首次使用需在设置中配置图片源目录
4. **导入图片**：自动从配置目录导入，或手动「批量导入」
5. **分析图片**：选择图片 → 「分析选中图片」→ 等待完成
6. **查看结果**：列表查看评分，点击卡片查看详情，使用筛选查找

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

### Q: Web 界面无法访问？

**A:** 确认后端（5000）和前端（5173）均已启动；检查端口占用与防火墙；查看 `logs/image_quality.log`。

### Q: 图片分析很慢？

**A:** 可在设置中关闭审美评分；若可用，使用 GPU 加速。

### Q: 如何配置AI模型？

**A:** 查看 [AI模型配置指南](../guides/ai-models.md)

### Q: 端口 5000 权限错误？

**A:** Windows 对部分端口有限制。可：① 以管理员权限运行 PowerShell 再启动；② 检查占用 `netstat -ano | findstr :5000`，必要时 `taskkill /PID XXXX /F`；③ 确认防火墙允许 Python 访问网络。详见 [启动指南](./STARTUP_GUIDE.md)。

## 启动文件说明

- **`scripts/run_web.py`** ⭐ 启动后端 API（Flask + WebSocket，端口 5000）
- **`app/`** 前端 React 应用，`npm run dev` 后访问 http://localhost:5173
- **`start.bat`** 🪟 Windows 一键启动（如已配置）
- **`scripts/start_project.ps1`** 💻 PowerShell 一键启动（如已配置）
- **`main.py`** 命令行工具入口（非 Web 界面）

详见 [启动指南](./STARTUP_GUIDE.md)。

## 下一步

- 📖 查看 [功能说明](../features/README.md) 了解所有功能
- 🏗️ 查看 [架构文档](../architecture/README.md) 了解项目结构
- 🔧 查看 [开发指南](../development/README.md) 参与开发

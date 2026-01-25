# Image Quality Analyzer

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

**一个专业的图像质量分析和评估工具**

批量计算图像质量指标，支持AI分析，并将结果保存到SQLite数据库和XMP元数据。

[功能特性](#-核心特性) • [快速开始](#-快速开始) • [文档](#-文档) • [贡献](#-贡献) • [许可证](#-许可证)

</div>

---

## 📖 简介

Image Quality Analyzer 是一个功能强大的图像质量分析工具，可以帮助您：

- 📊 **批量分析图像质量** - 自动计算模糊度、亮度、信息熵、BRISQUE等指标
- 🤖 **AI智能分析** - 支持GPT-4V、Claude、Gemini、Ollama等多种AI模型
- 🗄️ **数据持久化** - 结果保存到SQLite数据库，支持快速查询和统计
- 🏷️ **元数据管理** - 自动写入XMP元数据，兼容主流图像管理软件
- 🌐 **Web界面** - 现代化的Web界面，可视化查看和管理图像
- 🔍 **智能筛选** - 按质量分数、评级、标签等条件筛选图像

## ✨ 核心特性

### 📊 质量评估
- **模糊度检测** - Laplacian方差算法
- **亮度分析** - 平均亮度计算
- **信息熵** - 图像复杂度评估
- **BRISQUE分数** - 无参考图像质量评估（可选）
- **审美评分** - 基于CLIP或AI模型的审美评估

### 🤖 AI分析
- **多模型支持** - GPT-4V、Claude 3、Gemini、Ollama
- **自定义评估** - 支持自定义评估问题
- **内容描述** - 自动生成图像内容描述
- **质量评估** - AI驱动的质量评估

### 🗄️ 数据管理
- **SQLite存储** - 轻量级数据库，无需额外配置
- **快速查询** - 支持按多种条件查询
- **统计分析** - 自动生成质量统计报告
- **重复检测** - 基于哈希的重复图像检测

### 🏷️ 元数据支持
- **XMP Rating** - 1-5星评级（兼容Lightroom、Capture One等）
- **XMP Label** - 质量标签（高质量/中等质量/低质量等）
- **XMP Subject/Keywords** - 关键词列表（支持质量分析+AI提取，追加模式保留原有关键词）
- **XMP Description** - 详细指标和AI分析摘要（追加到现有描述，不覆盖）
- **标准XMP标签** - 使用Dublin Core和XMP Core标准，确保跨软件兼容
- **AI关键词提取** - 自动从AI分析中提取关键词，丰富元数据
- **元数据保护** ⚠️ - 绝对不覆盖个人信息、时间、地点、摄影参数等原有元数据

### 🌐 Web界面
- **现代化UI** - 响应式设计，支持多种视图
- **实时分析** - 支持实时分析和批量操作
- **图像预览** - 直接使用原图，快速加载
- **高级搜索** - 多条件组合搜索

## 🚀 快速开始

### 系统要求

- Python 3.10 或更高版本
- Windows / macOS / Linux
- 至少 2GB 可用内存
- 可选：GPU（用于CLIP模型审美评分）

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/xgs87762GH/image-quality-analyzer.git
cd image-quality-analyzer
```

#### 2. 创建虚拟环境（推荐）

```bash
# 使用 venv
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. ExifTool（自动解压，手动下载压缩包）

**系统会自动解压 `exiftool/` 目录中的压缩包，无需手动解压！**

- 手动下载ExifTool压缩包到 `exiftool/` 目录
- 启动项目时，系统会自动检测并解压压缩包
- 解压后的可执行文件会自动使用
- 解压成功后，压缩文件会自动清理

**下载地址**：
- **Windows**: https://exiftool.org/exiftool-XX.XX.zip
- **macOS/Linux**: https://exiftool.org/Image-ExifTool-XX.XX.tar.gz

**支持的压缩格式**：
- Windows: `.zip` 文件
- macOS/Linux: `.tar.gz` 或 `.tgz` 文件

**或者使用包管理器安装（可选）**：
- **Windows**: 下载并添加到系统PATH
- **macOS**: `brew install exiftool`
- **Linux**: `sudo apt-get install libimage-exiftool-perl`

> 注意：如果不安装ExifTool，系统仍可正常工作，但无法读取完整的EXIF/GPS元数据，也无法写入XMP元数据到图像文件。

ExifTool 用于读写XMP元数据。

**Windows:**
- 下载 [ExifTool](https://exiftool.org/) 
- 解压并添加到系统PATH

**macOS:**
```bash
brew install exiftool
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install libimage-exiftool-perl
```

#### 5. 初始化数据库

```bash
python scripts/init_database.py
```

### 启动Web界面

**方式一：仅后端（传统 Flask 界面）**

```bash
python scripts/run_web.py
```

然后在浏览器中访问：**http://localhost:5000**

**方式二：前端 + 后端同时启动（React 应用，推荐开发使用）**

```bash
# 1. 安装依赖（仅首次）
npm install
cd app && npm install

# 2. 在项目根目录一条命令同时启动
npm run dev
```

- 前端：**http://localhost:5173**
- 后端 API：**http://localhost:5000**

### 命令行使用

```bash
# 批量分析图片
python -m cli.main -i "图片目录路径"

# 查询高质量图片
python -m cli.query --rating 5

# 按元数据筛选
python -m cli.filter --rating 4 --output "高质量图片"
```

## 📁 项目结构

```
image-quality-analyzer/
├── analyzers/          # 分析器模块（质量分析、AI分析）
├── cli/               # 命令行接口
├── config/            # 配置管理
├── database/          # 数据库层（模型、迁移）
├── docs/              # 项目文档
├── metadata/          # 元数据处理（XMP读写）
├── processors/        # 批量处理器
├── repositories/      # 数据访问层（Repository模式）
├── services/          # 业务逻辑层
├── utils/             # 工具函数
├── web/               # Web界面（Flask应用）
└── scripts/           # 工具脚本
```

## 📚 文档

详细的文档已整理到 [docs/](./docs/) 目录：

### 📖 快速开始
- [快速开始指南](./docs/getting-started/README.md) - 安装和基本使用
- [启动指南](./docs/getting-started/STARTUP_GUIDE.md) - 详细启动说明和问题排查

### 📘 使用指南
- [Web界面使用指南](./docs/guides/web-interface.md) - Web界面详细操作
- [命令行使用指南](./docs/guides/command-line.md) - 命令行工具使用
- [AI模型配置指南](./docs/guides/ai-models.md) - 配置和使用AI模型
- [评估格式说明](./docs/guides/evaluation-format.md) - 评估问题格式

### 📗 功能说明
- [功能特性](./docs/features/README.md) - 所有功能详细说明

### 📕 架构和开发
- [项目架构](./docs/architecture/README.md) - 架构设计、目录结构和设计模式
- [开发指南](./docs/development/README.md) - 代码规范、扩展指南

**完整文档索引**: [docs/README.md](./docs/README.md)

## 🎯 使用场景

- 📸 **摄影师** - 批量评估照片质量，筛选高质量作品
- 🖼️ **图像管理** - 自动标记和分类图像，建立图像库
- 🔬 **质量检测** - 检测模糊、过曝、欠曝等问题图像
- 🤖 **AI训练** - 为AI模型准备高质量训练数据
- 📊 **数据分析** - 分析图像质量分布，生成统计报告

## 🔧 配置

### 环境变量

可以通过环境变量配置：

```bash
# 数据库路径
export DB_PATH="data/image_quality.db"

# 日志级别
export LOG_LEVEL="INFO"

# ExifTool路径
export EXIFTOOL_PATH="/usr/bin/exiftool"

# 是否使用审美评分
export USE_AESTHETIC="true"
```

### 配置文件

详细配置说明请参考 [配置文档](./docs/getting-started/README.md#配置)

## 🤝 贡献

我们欢迎所有形式的贡献！

- 🐛 报告Bug
- 💡 提出功能建议
- 📝 改进文档
- 💻 提交代码

请查看 [贡献指南](./CONTRIBUTING.md) 了解详细信息。

## 📝 更新日志

查看 [CHANGELOG.md](./CHANGELOG.md) 了解版本更新历史。

## 🔒 安全

如果您发现安全问题，请查看 [安全政策](./SECURITY.md)。

## 📄 许可证

本项目采用 [MIT 许可证](./LICENSE)。

## 🙏 致谢

感谢所有贡献者和使用者的支持！

## 📮 联系方式

- 📧 Issues: [GitHub Issues](https://github.com/xgs87762GH/image-quality-analyzer/issues)
- 📖 文档: [完整文档](./docs/README.md)

---

<div align="center">

**如果这个项目对您有帮助，请给个 ⭐ Star！**

Made with ❤️ by the Image Quality Analyzer team

</div>

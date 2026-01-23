# Scripts 目录说明

本目录包含项目的各种工具脚本。

## 启动脚本

### `run_web.py` ⭐
- **用途**: 启动Web界面
- **用法**: `python scripts/run_web.py`
- **说明**: 主启动方式，启动后访问 http://localhost:5000

### `start_project.ps1`
- **用途**: PowerShell一键启动脚本
- **用法**: `powershell -ExecutionPolicy Bypass -File scripts/start_project.ps1`
- **说明**: 自动处理环境激活、依赖检查、数据库初始化

## 数据库脚本

### `init_database.py`
- **用途**: 初始化数据库
- **用法**: `python scripts/init_database.py`
- **说明**: 首次使用前必须运行，创建数据库表结构

### `migrate_database.py`
- **用途**: 执行数据库迁移
- **用法**: `python scripts/migrate_database.py`
- **说明**: 当数据库结构更新时运行，添加新字段和表

## 工具脚本

### `view_log.py`
- **用途**: 查看日志文件
- **用法**: `python scripts/view_log.py [--file 日志路径] [--lines 行数]`
- **说明**: 方便查看项目日志，默认显示最后50行

### `fix_thumbnails.py` ⚠️ 已废弃
- **用途**: ~~修复现有图像的缩略图路径~~（已废弃）
- **用法**: `python scripts/fix_thumbnails.py`
- **说明**: 此脚本已废弃。系统现在直接使用原图，不再生成缩略图。保留此文件仅用于向后兼容。

## 环境设置脚本

### `setup_env.ps1` (Windows)
- **用途**: 创建conda环境并安装依赖
- **用法**: `powershell -ExecutionPolicy Bypass -File scripts/setup_env.ps1`
- **说明**: Windows环境设置脚本

### `setup_env.sh` (Linux/macOS)
- **用途**: 创建conda环境并安装依赖
- **用法**: `bash scripts/setup_env.sh`
- **说明**: Linux/macOS环境设置脚本

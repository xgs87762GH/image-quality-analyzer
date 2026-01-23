# 项目文件夹重命名指南

## 📋 重命名步骤

### 当前文件夹名
`filter_Image`

### 新文件夹名（推荐）
`image-quality-analyzer`

## 🔄 重命名操作

### Windows PowerShell

```powershell
# 1. 关闭所有正在运行的项目相关程序
# 2. 退出当前项目目录（如果正在其中）
cd ..

# 3. 重命名文件夹
Rename-Item -Path "filter_Image" -NewName "image-quality-analyzer"

# 4. 进入新目录
cd image-quality-analyzer
```

### Windows 资源管理器

1. 关闭所有正在运行的项目相关程序
2. 在文件资源管理器中找到项目文件夹
3. 右键点击 `filter_Image` 文件夹
4. 选择"重命名"
5. 输入新名称：`image-quality-analyzer`
6. 按 Enter 确认

### Linux/macOS

```bash
# 1. 关闭所有正在运行的项目相关程序
# 2. 退出当前项目目录（如果正在其中）
cd ..

# 3. 重命名文件夹
mv filter_Image image-quality-analyzer

# 4. 进入新目录
cd image-quality-analyzer
```

## ✅ 重命名后检查

### 1. 验证项目结构

```bash
# 检查关键文件是否存在
ls -la image-quality-analyzer/
ls -la image-quality-analyzer/scripts/
ls -la image-quality-analyzer/web/
```

### 2. 测试启动

```bash
# 激活conda环境
conda activate image_quality

# 测试启动Web服务
python scripts/run_web.py
```

### 3. 检查数据库路径

数据库文件位于 `data/image_quality.db`，使用相对路径，不受文件夹重命名影响。

### 4. 检查日志路径

日志文件位于 `logs/image_quality.log`，使用相对路径，不受文件夹重命名影响。

## ⚠️ 注意事项

### 1. 代码兼容性

✅ **无需修改代码** - 项目使用相对路径，所有路径都是相对于项目根目录的：
- 数据库：`data/image_quality.db`
- 日志：`logs/image_quality.log`
- 回收站：`trash/`
- 脚本路径：`scripts/run_web.py` 使用 `Path(__file__).parent.parent` 动态获取

### 2. 环境变量

如果设置了环境变量指向项目路径，需要更新：
- `PYTHONPATH`（如果设置了）
- IDE 的项目路径配置
- 快捷方式路径

### 3. Git 仓库

如果使用 Git，重命名文件夹后：
```bash
# Git 会自动检测文件夹重命名
git status

# 提交重命名
git add .
git commit -m "Rename project folder to image-quality-analyzer"
```

### 4. IDE 配置

如果使用 IDE（如 PyCharm、VSCode），可能需要：
- 重新打开项目
- 更新项目路径配置
- 重新配置 Python 解释器路径（如果使用绝对路径）

### 5. Conda 环境

Conda 环境名称 `image_quality` 不受影响，无需修改。

## 📝 更新后的文件

以下文件已更新为使用新项目名称：

- ✅ `README.md` - 项目标题和描述
- ✅ `PROJECT_NAME.md` - 项目命名说明
- ✅ `web/templates/*.html` - 所有页面标题
- ✅ `docs/*.md` - 文档中的项目名称
- ✅ `start.bat` - 启动脚本显示文本

## 🔍 验证清单

重命名后，请确认：

- [ ] 项目文件夹已成功重命名
- [ ] 可以正常启动 Web 服务（`python scripts/run_web.py`）
- [ ] 数据库文件可以正常访问
- [ ] 日志文件可以正常写入
- [ ] Web 界面可以正常访问（http://localhost:5000）
- [ ] 所有功能正常工作

## 🆘 如果遇到问题

### 问题1: 找不到模块

**错误**: `ModuleNotFoundError: No module named 'xxx'`

**解决**: 
- 确保在项目根目录运行命令
- 检查 Python 路径：`python -c "import sys; print(sys.path)"`

### 问题2: 数据库连接失败

**错误**: 无法连接数据库

**解决**:
- 检查 `data/image_quality.db` 文件是否存在
- 检查文件权限
- 重新初始化数据库：`python scripts/init_database.py`

### 问题3: 日志文件无法写入

**错误**: 日志文件无法创建

**解决**:
- 检查 `logs/` 目录是否存在
- 检查目录权限
- 手动创建目录：`mkdir logs`

## 📞 获取帮助

如果重命名后遇到其他问题，请：
1. 查看日志文件：`logs/image_quality.log`
2. 检查错误信息
3. 参考文档：`docs/getting-started/STARTUP_GUIDE.md`
4. 创建 Issue 描述问题

---

**最后更新**: 2026-01-23

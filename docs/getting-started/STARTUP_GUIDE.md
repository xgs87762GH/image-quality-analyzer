# 项目启动指南

## 🚀 快速启动

### 方式1: 直接启动（推荐）

```powershell
# 1. 激活conda环境
conda activate image_quality

# 2. 启动Web服务
python scripts/run_web.py
```

然后在浏览器访问：**http://localhost:5000**

### 方式2: 使用启动脚本（自动处理环境）

**Windows批处理:**
```cmd
start.bat
```

**PowerShell:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_project.ps1
```

## 📋 启动文件说明

### 主要启动文件

#### 1. `scripts/run_web.py` ⭐ **主启动方式**
- **用途**: 启动Web界面
- **端口**: 5000
- **命令**: `python scripts/run_web.py`
- **访问**: http://localhost:5000

#### 2. `start.bat` 🪟 **Windows批处理**
- **用途**: Windows一键启动（自动激活环境、检查依赖）
- **命令**: 双击运行或 `start.bat`
- **说明**: 自动处理环境激活和依赖检查

#### 3. `scripts/start_project.ps1` 💻 **PowerShell脚本**
- **用途**: PowerShell一键启动（自动激活环境、检查依赖）
- **命令**: `powershell -ExecutionPolicy Bypass -File scripts/start_project.ps1`
- **说明**: 自动处理环境激活和依赖检查

### 其他文件说明

#### `main.py`
- **用途**: 命令行工具入口
- **命令**: `python main.py -i "目录路径"`
- **说明**: 用于命令行批量处理图像，不是启动Web界面

## ⚠️ 常见问题

### 问题1: 端口权限错误 ⚠️

**错误信息**: "以一种访问权限不允许的方式做了一个访问套接字的尝试"

**原因分析**:
这是Windows系统对某些端口的访问限制，常见于：
- 端口5000在某些Windows版本需要管理员权限
- 端口被其他程序占用
- Windows防火墙阻止

**解决方案**（按优先级）:

**方案1: 以管理员权限运行**（推荐）
1. 右键点击 PowerShell
2. 选择"以管理员身份运行"
3. 然后运行：
   ```powershell
   conda activate image_quality
   python scripts/run_web.py
   ```

**方案2: 检查并关闭占用端口的进程**
```powershell
# 查看占用5000端口的进程
netstat -ano | findstr :5000

# 如果看到进程ID（PID），结束它（替换XXXX为实际PID）
taskkill /PID XXXX /F
```

**方案3: 使用其他端口**（临时方案）
如果必须使用5000端口，可以修改 `scripts/run_web.py`，将端口改为其他值（如8080）：
```python
app.run(host='127.0.0.1', port=8080, debug=True)
```
然后访问 http://localhost:8080

### 问题2: 端口被占用

**解决方案**:
```powershell
# 查看占用端口的进程
netstat -ano | findstr :5000

# 结束进程（替换XXXX为实际PID）
taskkill /PID XXXX /F
```

### 问题3: 环境未激活

**解决方案**:
```powershell
# 激活conda环境
conda activate image_quality

# 如果环境不存在，先创建
conda create -n image_quality python=3.10 -y
conda activate image_quality
pip install -r requirements.txt
```

### 问题4: Flask模块未找到

**解决方案**:
```powershell
# 确保已激活环境
conda activate image_quality

# 安装依赖
pip install -r requirements.txt
```

## 📝 完整启动流程

1. **激活conda环境**
   ```powershell
   conda activate image_quality
   ```

2. **检查依赖**（首次需要）
   ```powershell
   pip install -r requirements.txt
   ```

3. **初始化数据库**（首次需要）
   ```powershell
   python scripts/init_database.py
   ```

4. **启动Web服务**
   ```powershell
   python scripts/run_web.py
   ```

5. **访问界面**
   - 打开浏览器访问: http://localhost:5000

## 🎯 推荐启动命令

**最简单的方式**（如果环境已配置好）:

```powershell
conda activate image_quality && python scripts/run_web.py
```

## 📚 相关文档

- [快速开始指南](./README.md) - 安装和基本使用
- [Web界面使用指南](../guides/web-interface.md) - Web界面详细操作
- [命令行使用指南](../guides/command-line.md) - 命令行工具使用

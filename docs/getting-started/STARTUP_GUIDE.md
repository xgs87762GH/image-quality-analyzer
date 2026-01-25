# 项目启动指南

## 🚀 快速启动

项目为**前后端分离**：需分别启动后端 API 与前端应用。

### 1. 启动后端 API

```powershell
conda activate image_quality   # 或你的虚拟环境
python scripts/run_web.py
```

- **端口**: 5000（API + WebSocket）
- **说明**: 仅提供接口，浏览器不直接访问此地址

### 2. 启动前端应用

```powershell
cd app
npm install   # 首次需安装依赖
npm run dev
```

- **端口**: 5173
- **访问**: 在浏览器打开 **http://localhost:5173**

### 使用启动脚本（可选）

- **Windows 批处理**: `start.bat`
- **PowerShell**: `powershell -ExecutionPolicy Bypass -File scripts/start_project.ps1`

## 📋 启动文件说明

| 文件 | 用途 | 说明 |
|------|------|------|
| `scripts/run_web.py` | 后端 API | Flask + WebSocket，端口 5000 |
| `app/` 下 `npm run dev` | 前端界面 | React + Vite，端口 5173 |
| `start.bat` | Windows 一键启动 | 如已配置 |
| `scripts/start_project.ps1` | PowerShell 一键启动 | 如已配置 |
| `main.py` | 命令行工具 | 批量处理图像，非 Web 界面 |

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
修改 `scripts/run_web.py` 中 `socketio.run(..., port=5000)` 为其他端口（如 8080），并同步修改 `app/` 内 API 基地址（如 `vite.config` 或 `.env` 中的 `VITE_API_URL`），再访问对应前端地址。

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

4. **启动后端 API**
   ```powershell
   python scripts/run_web.py
   ```

5. **启动前端应用**（另开终端）
   ```powershell
   cd app && npm install && npm run dev
   ```

6. **访问界面**
   - 打开浏览器访问: http://localhost:5173

## 🎯 推荐启动命令

**后端**（环境已配置好）:

```powershell
conda activate image_quality && python scripts/run_web.py
```

**前端**（另开终端）:

```powershell
cd app && npm run dev
```

## 📚 相关文档

- [快速开始指南](./README.md) - 安装和基本使用
- [Web 界面使用指南](../guides/web-interface.md) - Web 界面详细操作
- [命令行使用指南](../guides/command-line.md) - 命令行工具使用

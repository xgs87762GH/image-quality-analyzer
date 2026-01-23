@echo off
chcp 65001 >nul
REM 快速启动脚本（Windows批处理）

echo ========================================
echo   Image Quality Analyzer - 启动
echo   图像质量分析器
echo ========================================
echo.

REM 激活conda环境
call conda activate image_quality
if errorlevel 1 (
    echo 错误: 无法激活conda环境
    echo 请先创建环境: conda create -n image_quality python=3.10 -y
    pause
    exit /b 1
)

REM 检查依赖
python -c "import flask" 2>nul
if errorlevel 1 (
    echo 安装依赖...
    pip install -r requirements.txt
)

REM 检查数据库
if not exist "data\image_quality.db" (
    echo 初始化数据库...
    python scripts\init_database.py
)

echo.
echo ========================================
echo   启动Web服务器...
echo ========================================
echo 访问地址: http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo.

REM 启动Web服务器
python scripts\run_web.py

pause

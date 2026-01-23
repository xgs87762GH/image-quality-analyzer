@echo off
REM 运行 Ollama 测试脚本

echo ========================================
echo   Ollama API 测试
echo ========================================
echo.

REM 激活conda环境
call conda activate image_quality
if errorlevel 1 (
    echo 错误: 无法激活conda环境 image_quality
    echo 请先创建环境: conda create -n image_quality python=3.10 -y
    pause
    exit /b 1
)

REM 检查并安装 requests
python -c "import requests" 2>nul
if errorlevel 1 (
    echo 正在安装 requests 库...
    pip install requests
)

echo.
echo 运行测试脚本...
echo.

REM 运行测试
python tests\test_ollama_direct.py

pause

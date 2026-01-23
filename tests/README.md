# 测试目录

本目录包含所有测试脚本和测试相关文件。

## 测试文件说明

### Ollama API 测试
- `test_ollama_direct.py` - 直接测试 Ollama API（推荐使用）
- `test_ollama_simple.py` - 简单的 Ollama API 测试脚本
- `test_ollama_api.py` - 完整的 Ollama API 测试工具
- `test_ollama_curl.ps1` - PowerShell 测试脚本
- `test_ollama_curl.sh` - Bash 测试脚本
- `test_ollama_manual.md` - 手动测试指南

### 其他测试
- `test_analyzer.py` - 图像分析器测试
- `run_test.bat` - Windows 批处理测试脚本

## 使用方法

### 测试 Ollama API（使用原图）
```bash
python tests/test_ollama_direct.py
```

### 测试 Ollama API（使用缩略图，更快）
```bash
python tests/test_ollama_direct.py --thumbnail
```

### 测试指定图片
```bash
python tests/test_ollama_direct.py --image "path/to/image.jpg"
```

## 注意事项

1. 测试前确保 Ollama 服务正在运行
2. 确保已安装 `requests` 库：`pip install requests`
3. 大图片测试可能需要较长时间，请耐心等待

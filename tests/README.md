# 测试目录

## ExifTool 测试

```bash
# 基础测试
python tests/test_exiftool.py

# 诊断工具
python tests/diagnose_exiftool.py
```

## Ollama API 测试

```bash
# 直接测试（推荐）
python tests/test_ollama_direct.py

# 使用缩略图（更快）
python tests/test_ollama_direct.py --thumbnail
```

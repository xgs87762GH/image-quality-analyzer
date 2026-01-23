# Ollama API 测试指南

## 使用 curl 测试 Ollama API

### 方法 1: 使用生成的 JSON 文件

1. 运行测试脚本生成 curl 命令：
```bash
python test_ollama_simple.py --curl-only
```

2. 脚本会生成一个 JSON 文件路径，例如：
```
C:\Users\xgs\AppData\Local\Temp\tmpXXXXXX.json
```

3. 使用 curl 命令测试：
```bash
curl -X POST http://localhost:11434/api/generate ^
  -H "Content-Type: application/json" ^
  -d @C:\Users\xgs\AppData\Local\Temp\tmpXXXXXX.json
```

### 方法 2: 使用 PowerShell 测试

运行 PowerShell 脚本：
```powershell
powershell -ExecutionPolicy Bypass -File test_ollama_curl.ps1
```

### 方法 3: 手动构建请求

1. 将图片编码为 base64：
```powershell
$imageBytes = [System.IO.File]::ReadAllBytes("图片路径.jpg")
$imageBase64 = [System.Convert]::ToBase64String($imageBytes)
```

2. 构建 JSON 请求体：
```json
{
  "model": "qwen3vl",
  "prompt": "请分析这张图片，提供以下信息：\n1. 图片质量评估（清晰度、色彩、构图等）\n2. 主要内容描述\n3. 可能的用途或场景\n4. 改进建议（如果有）\n\n请用中文回答。",
  "stream": false,
  "images": ["<base64编码的图片>"]
}
```

3. 使用 curl 发送请求：
```bash
curl -X POST http://localhost:11434/api/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"qwen3vl\",\"prompt\":\"请分析这张图片\",\"stream\":false,\"images\":[\"<base64>\"]}"
```

## 检查要点

1. **模型名称**: 确保使用正确的视觉模型（如 `qwen3vl`）
2. **images 字段**: 必须是 base64 编码的字符串数组
3. **API 端点**: 使用 `/api/generate`（不是 `/api/chat`）
4. **Content-Type**: 必须是 `application/json`

## 常见问题

- **连接错误**: 确保 Ollama 服务正在运行（`ollama serve`）
- **模型未找到**: 确保模型已下载（`ollama pull qwen3vl`）
- **超时**: 视觉模型处理可能需要较长时间，增加超时时间
- **空响应**: 检查模型是否正确加载，查看 Ollama 日志

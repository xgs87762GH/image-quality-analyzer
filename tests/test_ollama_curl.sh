#!/bin/bash
# 测试 Ollama API 的 curl 命令

# 配置
OLLAMA_URL="http://localhost:11434"
MODEL="qwen3vl"
IMAGE_PATH="thumbnails/10861b4a328752d43035472a90f5e23d.jpg"

# 检查图片是否存在
if [ ! -f "$IMAGE_PATH" ]; then
    echo "错误: 图片文件不存在: $IMAGE_PATH"
    exit 1
fi

# 将图片编码为 base64
echo "正在编码图片为 base64..."
IMAGE_BASE64=$(base64 -w 0 "$IMAGE_PATH" 2>/dev/null || base64 "$IMAGE_PATH" | tr -d '\n')

# 构建 JSON 请求
PROMPT="请分析这张图片，提供以下信息：
1. 图片质量评估（清晰度、色彩、构图等）
2. 主要内容描述
3. 可能的用途或场景
4. 改进建议（如果有）

请用中文回答。"

# 创建临时 JSON 文件
TEMP_JSON=$(mktemp)
cat > "$TEMP_JSON" <<EOF
{
  "model": "$MODEL",
  "prompt": "$PROMPT",
  "stream": false,
  "images": ["$IMAGE_BASE64"]
}
EOF

echo "发送请求到 Ollama..."
echo "URL: $OLLAMA_URL/api/generate"
echo "模型: $MODEL"
echo ""

# 发送请求
curl -X POST "$OLLAMA_URL/api/generate" \
  -H "Content-Type: application/json" \
  -d @"$TEMP_JSON" \
  --max-time 180 \
  -w "\n\nHTTP状态码: %{http_code}\n总时间: %{time_total}秒\n"

# 清理临时文件
rm -f "$TEMP_JSON"

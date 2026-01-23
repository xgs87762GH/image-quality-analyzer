# PowerShell 脚本：测试 Ollama API
# 测试 Ollama API 的 curl 命令

# 配置
$OLLAMA_URL = "http://localhost:11434"
$MODEL = "qwen3vl"
$IMAGE_PATH = "thumbnails\10861b4a328752d43035472a90f5e23d.jpg"

# 检查图片是否存在
if (-not (Test-Path $IMAGE_PATH)) {
    Write-Host "错误: 图片文件不存在: $IMAGE_PATH" -ForegroundColor Red
    exit 1
}

Write-Host "正在编码图片为 base64..." -ForegroundColor Yellow

# 读取图片并编码为 base64
$imageBytes = [System.IO.File]::ReadAllBytes($IMAGE_PATH)
$imageBase64 = [System.Convert]::ToBase64String($imageBytes)

# 构建提示词
$prompt = @"
请分析这张图片，提供以下信息：
1. 图片质量评估（清晰度、色彩、构图等）
2. 主要内容描述
3. 可能的用途或场景
4. 改进建议（如果有）

请用中文回答。
"@

# 构建 JSON 请求体
$requestBody = @{
    model = $MODEL
    prompt = $prompt
    stream = $false
    images = @($imageBase64)
} | ConvertTo-Json -Depth 10

# 创建临时 JSON 文件
$tempJson = [System.IO.Path]::GetTempFileName() + ".json"
$requestBody | Out-File -FilePath $tempJson -Encoding UTF8

Write-Host ""
Write-Host "发送请求到 Ollama..." -ForegroundColor Yellow
Write-Host "URL: $OLLAMA_URL/api/generate" -ForegroundColor Cyan
Write-Host "模型: $MODEL" -ForegroundColor Cyan
Write-Host "图片大小: $($imageBytes.Length) 字节" -ForegroundColor Cyan
Write-Host "Base64 长度: $($imageBase64.Length) 字符" -ForegroundColor Cyan
Write-Host ""

# 发送请求
try {
    $response = Invoke-RestMethod -Uri "$OLLAMA_URL/api/generate" `
        -Method Post `
        -ContentType "application/json" `
        -Body $requestBody `
        -TimeoutSec 180
    
    Write-Host "请求成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "响应内容:" -ForegroundColor Yellow
    Write-Host ("-" * 60)
    
    if ($response.error) {
        Write-Host "错误: $($response.error)" -ForegroundColor Red
    } elseif ($response.response) {
        Write-Host $response.response -ForegroundColor White
        Write-Host ""
        Write-Host ("-" * 60)
        Write-Host "响应长度: $($response.response.Length) 字符" -ForegroundColor Cyan
    } else {
        Write-Host "警告: 响应中没有 'response' 字段" -ForegroundColor Yellow
        Write-Host ($response | ConvertTo-Json -Depth 10)
    }
    
} catch {
    Write-Host "请求失败: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "错误响应: $responseBody" -ForegroundColor Red
    }
} finally {
    # 清理临时文件
    if (Test-Path $tempJson) {
        Remove-Item $tempJson -Force
    }
}

Write-Host ""
Write-Host "提示: 你也可以使用以下 curl 命令测试:" -ForegroundColor Cyan
Write-Host "curl -X POST $OLLAMA_URL/api/generate -H 'Content-Type: application/json' -d `"@$tempJson`""

# AI模型配置指南

本文档说明如何配置和使用各种AI模型进行图像分析。

## 📋 目录

- [支持的模型](#支持的模型)
- [Ollama配置](#ollama配置)
- [云端模型配置](#云端模型配置)
- [使用示例](#使用示例)

## 支持的模型

### 1. Ollama (本地模型) ⭐推荐

**优势**:
- 完全本地化，无需API密钥
- 数据隐私安全
- 无使用费用
- 支持离线使用

**推荐模型**:
- `llava` - 强大的视觉理解能力
- `qwen2-vl` - 中文支持好
- `qwen3-vl` - 最新版本
- `bakllava` - 轻量级选择

### 2. GPT-4 Vision (OpenAI)

**优势**:
- 强大的图像理解能力
- 准确的分析结果

**需要**:
- OpenAI API密钥
- 网络连接

### 3. Claude 3 (Anthropic)

**优势**:
- 优秀的图像分析能力
- 详细的描述

**需要**:
- Anthropic API密钥
- 网络连接

### 4. Gemini Pro Vision (Google)

**优势**:
- 多模态理解能力
- 性价比高

**需要**:
- Google API密钥
- 网络连接

## Ollama配置

### 安装Ollama

#### Windows

1. 访问 https://ollama.ai
2. 下载Windows安装程序
3. 运行安装程序
4. Ollama会自动在后台运行（默认端口：11434）

#### macOS

```bash
brew install ollama
ollama serve
```

#### Linux

```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
```

### 下载模型

#### 推荐视觉模型（支持图像分析）

```bash
# Llava模型（推荐）
ollama pull llava

# Qwen2-VL模型（中文支持好）
ollama pull qwen2-vl

# Qwen3-VL模型（最新）
ollama pull qwen3-vl

# Bakllava模型（轻量级）
ollama pull bakllava
```

#### 查看已安装的模型

```bash
ollama list
```

### 配置Web界面

1. 打开Web界面设置
2. 选择"AI模型设置"标签
3. 选择"Ollama (本地)"
4. 配置Ollama API地址（默认：http://localhost:11434）
5. 选择要使用的模型（如：llava）
6. 保存设置

### 测试连接

在Web界面中：
1. 选择一张图片
2. 点击"AI分析"
3. 查看分析结果

如果失败，检查：
- Ollama服务是否运行
- API地址是否正确
- 模型是否已下载

## 云端模型配置

### GPT-4 Vision

1. **获取API密钥**
   - 访问 https://platform.openai.com
   - 注册/登录账号
   - 创建API密钥

2. **配置Web界面**
   - 选择"AI模型设置"
   - 选择"GPT-4 Vision"
   - 输入API密钥
   - 保存设置

### Claude 3

1. **获取API密钥**
   - 访问 https://console.anthropic.com
   - 注册/登录账号
   - 创建API密钥

2. **配置Web界面**
   - 选择"AI模型设置"
   - 选择"Claude 3"
   - 输入API密钥
   - 保存设置

### Gemini Pro Vision

1. **获取API密钥**
   - 访问 https://makersuite.google.com/app/apikey
   - 注册/登录账号
   - 创建API密钥

2. **配置Web界面**
   - 选择"AI模型设置"
   - 选择"Gemini Pro Vision"
   - 输入API密钥
   - 保存设置

## 使用示例

### 基本AI分析

1. 在图像列表中选择图片
2. 点击"AI分析"按钮
3. 等待分析完成
4. 查看分析结果

### 自定义评估问题

1. 打开设置
2. 选择"自定义评估问题"标签
3. 输入评估问题，例如："是否为手机截图"
4. 选择答案格式，例如："是/否"
5. 保存设置
6. 分析图片时，AI会回答该问题

### 审美评估

1. 打开设置
2. 选择"基础设置"标签
3. 选择"审美评估方式"为"基于所选AI模型评估审美"
4. 确保已配置AI模型
5. 保存设置
6. 分析图片时，会使用AI模型评估审美

## 模型选择建议

### 根据需求选择

- **隐私要求高**: 使用Ollama本地模型
- **分析准确性要求高**: 使用GPT-4 Vision或Claude 3
- **成本考虑**: 使用Ollama或Gemini
- **中文支持**: 使用Ollama的qwen系列模型

### 根据资源选择

- **有GPU**: 使用Ollama本地模型，速度快
- **无GPU但网络好**: 使用云端模型
- **网络不稳定**: 使用Ollama本地模型

## 常见问题

### Q: Ollama连接失败？

**A:**
- 检查Ollama服务是否运行：`ollama list`
- 检查端口是否正确（默认11434）
- 检查防火墙设置
- 如果Ollama在其他机器，修改API地址为对应IP

### Q: 模型下载很慢？

**A:**
- 使用国内镜像（如果可用）
- 选择较小的模型（如bakllava）
- 使用代理加速

### Q: API密钥无效？

**A:**
- 检查密钥是否正确复制
- 检查密钥是否过期
- 检查账户余额（某些服务需要）

### Q: 分析结果不准确？

**A:**
- 尝试不同的模型
- 使用更详细的提示词
- 检查图像质量（模糊图像可能影响分析）

## 性能优化

1. **使用本地模型**: Ollama本地模型通常比云端模型快
2. **选择合适的模型**: 较小的模型速度更快，但准确性可能略低
3. **批量分析**: 使用批量分析功能提高效率
4. **并发控制**: 后端默认并发数为1，可根据系统资源调整后端配置

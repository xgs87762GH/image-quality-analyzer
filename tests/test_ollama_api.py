#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 Ollama API 请求"""
import base64
import json
import requests
import sys
from pathlib import Path

def test_ollama_api(image_path: str, model: str = "qwen3vl", base_url: str = "http://localhost:11434"):
    """
    测试 Ollama API 请求
    
    Args:
        image_path: 图像文件路径
        model: Ollama 模型名称
        base_url: Ollama API 地址
    """
    print(f"测试 Ollama API")
    print(f"  图像路径: {image_path}")
    print(f"  模型: {model}")
    print(f"  API 地址: {base_url}")
    print("-" * 60)
    
    # 1. 检查文件是否存在
    if not Path(image_path).exists():
        print(f"❌ 错误: 图像文件不存在: {image_path}")
        return False
    
    # 2. 读取图像并编码为 base64
    try:
        print("📖 读取图像文件...")
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
            image_data = base64.b64encode(image_bytes).decode('utf-8')
        print(f"✓ 图像读取成功，大小: {len(image_bytes)} 字节")
        print(f"  Base64 编码长度: {len(image_data)} 字符")
    except Exception as e:
        print(f"❌ 读取图像文件失败: {e}")
        return False
    
    # 3. 构建请求数据
    prompt = """请分析这张图片，提供以下信息：
1. 图片质量评估（清晰度、色彩、构图等）
2. 主要内容描述
3. 可能的用途或场景
4. 改进建议（如果有）

请用中文回答。"""
    
    request_data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "images": [image_data]  # 视觉模型需要 images 字段
    }
    
    print(f"\n📤 发送请求到: {base_url}/api/generate")
    print(f"  模型: {model}")
    print(f"  提示词长度: {len(prompt)} 字符")
    print(f"  包含图像: 是")
    
    # 4. 发送请求
    try:
        print("\n⏳ 等待响应...")
        response = requests.post(
            f"{base_url}/api/generate",
            json=request_data,
            timeout=180
        )
        
        print(f"\n📥 响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API 错误:")
            print(f"  状态码: {response.status_code}")
            print(f"  响应内容: {response.text[:500]}")
            return False
        
        # 5. 解析响应
        try:
            result = response.json()
            
            print(f"\n✅ 响应解析成功")
            print(f"  响应键: {list(result.keys())}")
            
            # 检查错误
            if 'error' in result:
                print(f"\n❌ Ollama 返回错误:")
                print(f"  {result['error']}")
                return False
            
            # 获取分析结果
            analysis_text = result.get('response', '')
            
            if not analysis_text:
                print(f"\n⚠️  警告: 响应中没有 'response' 字段或为空")
                print(f"  完整响应: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
                return False
            
            print(f"\n📝 分析结果:")
            print(f"  长度: {len(analysis_text)} 字符")
            print(f"  内容预览:")
            print("-" * 60)
            print(analysis_text[:500])
            if len(analysis_text) > 500:
                print(f"... (还有 {len(analysis_text) - 500} 字符)")
            print("-" * 60)
            
            # 显示其他响应信息
            if 'total_duration' in result:
                print(f"\n⏱️  处理时间: {result['total_duration'] / 1e9:.2f} 秒")
            if 'load_duration' in result:
                print(f"  模型加载时间: {result['load_duration'] / 1e9:.2f} 秒")
            if 'prompt_eval_count' in result:
                print(f"  提示词 token 数: {result['prompt_eval_count']}")
            if 'eval_count' in result:
                print(f"  生成 token 数: {result['eval_count']}")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON 解析失败: {e}")
            print(f"  响应内容: {response.text[:1000]}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ 连接错误: {e}")
        print(f"  请确保 Ollama 服务正在运行: {base_url}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"\n❌ 请求超时: {e}")
        print(f"  模型可能需要更长时间处理，请重试")
        return False
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_curl_command(image_path: str, model: str = "qwen3vl", base_url: str = "http://localhost:11434"):
    """
    生成 curl 命令用于测试
    
    Args:
        image_path: 图像文件路径
        model: Ollama 模型名称
        base_url: Ollama API 地址
    """
    print(f"\n📋 生成 curl 测试命令:")
    print("-" * 60)
    
    # 读取图像并编码
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
            image_data = base64.b64encode(image_bytes).decode('utf-8')
    except Exception as e:
        print(f"❌ 无法读取图像: {e}")
        return
    
    prompt = """请分析这张图片，提供以下信息：
1. 图片质量评估（清晰度、色彩、构图等）
2. 主要内容描述
3. 可能的用途或场景
4. 改进建议（如果有）

请用中文回答。"""
    
    request_data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "images": [image_data]
    }
    
    # 将请求数据保存到临时文件
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(request_data, f, ensure_ascii=False, indent=2)
        temp_file = f.name
    
    print(f"curl -X POST {base_url}/api/generate \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -d @{temp_file}")
    print(f"\n或者使用内联 JSON:")
    print(f"curl -X POST {base_url}/api/generate \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -d '{json.dumps(request_data, ensure_ascii=False)}'")
    
    print(f"\n💡 提示: 请求数据已保存到: {temp_file}")
    print(f"   你可以手动编辑此文件后使用上面的 curl 命令测试")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试 Ollama API")
    parser.add_argument("image", help="图像文件路径")
    parser.add_argument("--model", default="qwen3vl", help="Ollama 模型名称 (默认: qwen3vl)")
    parser.add_argument("--base-url", default="http://localhost:11434", help="Ollama API 地址 (默认: http://localhost:11434)")
    parser.add_argument("--curl", action="store_true", help="只生成 curl 命令，不执行测试")
    
    args = parser.parse_args()
    
    if args.curl:
        generate_curl_command(args.image, args.model, args.base_url)
    else:
        success = test_ollama_api(args.image, args.model, args.base_url)
        if success:
            print(f"\n✅ 测试成功！")
            sys.exit(0)
        else:
            print(f"\n❌ 测试失败！")
            sys.exit(1)

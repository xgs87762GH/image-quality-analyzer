#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简单的 Ollama API 测试脚本"""
import base64
import json
import sys
import tempfile
from pathlib import Path

# 设置控制台编码
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 尝试导入 requests，如果没有则只生成 curl 命令
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("警告: requests 模块未安装，将只生成 curl 命令")

def generate_curl_command(image_path: str, model: str = "qwen3vl", base_url: str = "http://localhost:11434"):
    """生成 curl 测试命令"""
    
    if not Path(image_path).exists():
        print(f"错误: 图片文件不存在: {image_path}")
        return None
    
    # 读取图片并编码
    print(f"读取图片: {image_path}")
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
        image_data = base64.b64encode(image_bytes).decode('utf-8')
    
    print(f"图片大小: {len(image_bytes)} 字节")
    print(f"Base64 长度: {len(image_data)} 字符")
    
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
    
    # 保存到临时文件
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
    json.dump(request_data, temp_file, ensure_ascii=False, indent=2)
    temp_file.close()
    
    print(f"\ncurl 测试命令:")
    print("-" * 60)
    print(f"curl -X POST {base_url}/api/generate \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -d @{temp_file.name}")
    print("-" * 60)
    print(f"\nJSON 文件已保存到: {temp_file.name}")
    print(f"你可以手动编辑此文件后使用上面的 curl 命令")
    
    return temp_file.name

def test_with_requests(image_path: str, model: str = "qwen3vl", base_url: str = "http://localhost:11434"):
    """使用 requests 库测试"""
    if not HAS_REQUESTS:
        print("错误: requests 模块未安装，无法执行测试")
        return False
    
    if not Path(image_path).exists():
        print(f"错误: 图片文件不存在: {image_path}")
        return False
    
    print(f"\n使用 Python requests 测试...")
    
    # 读取图片
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
        image_data = base64.b64encode(image_bytes).decode('utf-8')
    
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
    
    print(f"发送请求到: {base_url}/api/generate")
    print(f"模型: {model}")
    
    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json=request_data,
            timeout=180
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"错误响应: {response.text[:500]}")
            return False
        
        result = response.json()
        
        if 'error' in result:
            print(f"Ollama 错误: {result['error']}")
            return False
        
        analysis = result.get('response', '')
        if not analysis:
            print(f"警告: 响应为空")
            print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
            return False
        
        print(f"\n测试成功！")
        print(f"分析结果 ({len(analysis)} 字符):")
        print("-" * 60)
        print(analysis[:500])
        if len(analysis) > 500:
            print(f"... (还有 {len(analysis) - 500} 字符)")
        print("-" * 60)
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试 Ollama API")
    parser.add_argument("image", nargs="?", help="图像文件路径（可选）")
    parser.add_argument("--model", default="qwen3vl", help="Ollama 模型名称")
    parser.add_argument("--base-url", default="http://localhost:11434", help="Ollama API 地址")
    parser.add_argument("--curl-only", action="store_true", help="只生成 curl 命令，不执行测试")
    
    args = parser.parse_args()
    
    # 如果没有指定图片，尝试使用数据库中的第一张图片
    if not args.image:
        try:
            from database.connection import get_db
            from repositories.image_repository import ImageRepository
            
            db = get_db()
            repo = ImageRepository(db)
            img = repo.find_by_id(1)
            
            if img and Path(img.file_path).exists():
                args.image = img.file_path
                print(f"使用数据库中的图片: {args.image}")
            else:
                print("错误: 请指定图片路径")
                print("用法: python test_ollama_simple.py <图片路径>")
                sys.exit(1)
        except Exception as e:
            print(f"无法从数据库获取图片: {e}")
            print("请手动指定图片路径")
            sys.exit(1)
    
    if args.curl_only or not HAS_REQUESTS:
        generate_curl_command(args.image, args.model, args.base_url)
    else:
        # 先生成 curl 命令
        json_file = generate_curl_command(args.image, args.model, args.base_url)
        print("\n" + "=" * 60)
        # 然后执行测试
        success = test_with_requests(args.image, args.model, args.base_url)
        sys.exit(0 if success else 1)

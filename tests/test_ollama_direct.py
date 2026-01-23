#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接测试 Ollama API（使用 requests 库）"""
import base64
import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("错误: 需要安装 requests 库")
    print("请运行: pip install requests")
    sys.exit(1)

# 设置控制台编码
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

def test_ollama(image_path=None, use_thumbnail=False):
    """测试 Ollama API"""
    
    # 选择图片
    if use_thumbnail:
        # 使用缩略图（更小，测试更快）
        thumb_path = Path("thumbnails/10861b4a328752d43035472a90f5e23d.jpg")
        if thumb_path.exists():
            image_path = str(thumb_path)
            print(f"使用缩略图: {image_path}")
        else:
            print("错误: 缩略图不存在")
            return False
    elif not image_path:
        # 从数据库获取图片路径
        try:
            import sys
            from pathlib import Path
            # 添加项目根目录到路径
            project_root = Path(__file__).parent.parent
            sys.path.insert(0, str(project_root))
            
            from database.connection import get_db
            from repositories.image_repository import ImageRepository
            
            db = get_db()
            repo = ImageRepository(db)
            img = repo.find_by_id(1)
            
            if not img:
                print("错误: 数据库中没有图片")
                return False
            
            image_path = img.file_path
            if not Path(image_path).exists():
                print(f"错误: 图片文件不存在: {image_path}")
                return False
            
            print(f"使用数据库中的图片: {image_path}")
        except Exception as e:
            print(f"无法从数据库获取图片: {e}")
            return False
    
    if not Path(image_path).exists():
        print(f"错误: 图片文件不存在: {image_path}")
        return False
    
    # 配置
    OLLAMA_URL = "http://localhost:11434"
    # 从 API 获取实际模型名称
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            models = [m['name'] for m in data.get('models', [])]
            if models:
                MODEL = models[0]  # 使用第一个可用模型
                print(f"检测到模型: {MODEL}")
            else:
                MODEL = "qwen3-vl:8b"  # 默认模型
                print(f"使用默认模型: {MODEL}")
        else:
            MODEL = "qwen3-vl:8b"  # 默认模型
            print(f"无法获取模型列表，使用默认: {MODEL}")
    except:
        MODEL = "qwen3-vl:8b"  # 默认模型
        print(f"无法获取模型列表，使用默认: {MODEL}")
    
    print(f"\n配置:")
    print(f"  Ollama URL: {OLLAMA_URL}")
    print(f"  模型: {MODEL}")
    print(f"  图片: {image_path}")
    
    # 读取图片
    print(f"\n读取图片...")
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
            image_data = base64.b64encode(image_bytes).decode('utf-8')
        print(f"  图片大小: {len(image_bytes)} 字节 ({len(image_bytes)/1024/1024:.2f} MB)")
        print(f"  Base64 长度: {len(image_data)} 字符 ({len(image_data)/1024/1024:.2f} MB)")
        
        # 检查大小
        if len(image_data) > 10 * 1024 * 1024:  # 10MB
            print(f"  警告: Base64 编码后的数据很大，可能导致请求失败")
    except Exception as e:
        print(f"错误: 读取图片失败: {e}")
        return False
    
    # 构建请求
    prompt = """请分析这张图片，提供以下信息：
1. 图片质量评估（清晰度、色彩、构图等）
2. 主要内容描述
3. 可能的用途或场景
4. 改进建议（如果有）

请用中文回答。"""
    
    request_data = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "images": [image_data]
    }
    
    print(f"\n发送请求到: {OLLAMA_URL}/api/generate")
    print(f"  模型: {MODEL}")
    print(f"  包含图片: 是")
    print(f"  请求体大小: {len(json.dumps(request_data)) / 1024 / 1024:.2f} MB")
    print(f"  等待响应（可能需要较长时间，请耐心等待）...")
    
    try:
        # 使用 requests 发送请求（对大文件处理更好）
        print(f"  正在连接并发送请求...")
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=request_data,
            timeout=300,  # 5分钟超时（大图片处理需要更长时间）
            stream=False  # 不使用流式响应
        )
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"\n错误: HTTP {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            return False
        
        result = response.json()
        
        print(f"\n响应键: {list(result.keys())}")
        
        if 'error' in result:
            print(f"\n错误: {result['error']}")
            return False
        
        analysis = result.get('response', '')
        if not analysis:
            print(f"\n警告: 响应中没有 'response' 字段或为空")
            print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
            return False
        
        print(f"\n成功!")
        print(f"分析结果长度: {len(analysis)} 字符")
        print(f"\n分析结果:")
        print("-" * 60)
        print(analysis)
        print("-" * 60)
        
        # 显示其他信息
        if 'total_duration' in result:
            print(f"\n处理时间: {result['total_duration'] / 1e9:.2f} 秒")
        if 'load_duration' in result:
            print(f"模型加载时间: {result['load_duration'] / 1e9:.2f} 秒")
        if 'eval_count' in result:
            print(f"生成 token 数: {result['eval_count']}")
        
        return True
        
    except requests.exceptions.ConnectionError as e:
        print(f"\n连接错误: {e}")
        print(f"请确保 Ollama 服务正在运行: {OLLAMA_URL}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"\n请求超时: {e}")
        print(f"大图片处理可能需要更长时间，请重试或使用较小的图片")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n请求失败: {e}")
        return False
    except Exception as e:
        print(f"\n请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试 Ollama API（默认使用原图）")
    parser.add_argument("--thumbnail", action="store_true", help="使用缩略图测试（更快）")
    parser.add_argument("--image", help="指定图片路径（默认从数据库获取原图）")
    
    args = parser.parse_args()
    
    # 默认使用原图，除非指定 --thumbnail
    success = test_ollama(image_path=args.image, use_thumbnail=args.thumbnail)
    sys.exit(0 if success else 1)

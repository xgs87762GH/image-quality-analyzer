"""系统信息工具"""
import platform
import sys
from typing import Dict, Any, Optional
from pathlib import Path


def get_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    info = {
        'platform': {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': sys.version,
            'python_executable': sys.executable
        },
        'gpu': get_gpu_info(),
        'models': get_models_info(),
        'memory': get_memory_info()
    }
    return info


def get_gpu_info() -> Dict[str, Any]:
    """获取GPU信息"""
    gpu_info = {
        'available': False,
        'cuda_available': False,
        'cuda_version': None,
        'gpu_name': None,
        'gpu_count': 0,
        'gpu_details': []
    }
    
    # 检查PyTorch CUDA
    try:
        import torch
        gpu_info['cuda_available'] = torch.cuda.is_available()
        if gpu_info['cuda_available']:
            gpu_info['available'] = True
            gpu_info['cuda_version'] = torch.version.cuda
            gpu_info['gpu_count'] = torch.cuda.device_count()
            gpu_info['gpu_details'] = []
            for i in range(gpu_info['gpu_count']):
                gpu_info['gpu_details'].append({
                    'index': i,
                    'name': torch.cuda.get_device_name(i),
                    'memory_total': f"{torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB",
                    'memory_allocated': f"{torch.cuda.memory_allocated(i) / 1024**3:.2f} GB" if torch.cuda.is_available() else "0 GB"
                })
                gpu_info['gpu_name'] = torch.cuda.get_device_name(0)  # 第一个GPU名称
    except ImportError:
        pass
    
    # 如果没有PyTorch，尝试使用nvidia-smi
    if not gpu_info['available']:
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                gpu_info['available'] = True
                gpu_info['gpu_count'] = len(lines)
                gpu_info['gpu_details'] = []
                for i, line in enumerate(lines):
                    parts = line.split(',')
                    if len(parts) >= 2:
                        gpu_info['gpu_details'].append({
                            'index': i,
                            'name': parts[0].strip(),
                            'memory_total': parts[1].strip()
                        })
                        if i == 0:
                            gpu_info['gpu_name'] = parts[0].strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    return gpu_info


def get_models_info() -> Dict[str, Any]:
    """获取模型信息"""
    models_info = {
        'aesthetic': {
            'available': False,
            'model_name': None,
            'model_path': None,
            'downloaded': False,
            'size': None
        }
    }
    
    # 检查CLIP模型
    try:
        from transformers import CLIPProcessor, CLIPModel
        from pathlib import Path
        import os
        
        model_name = "openai/clip-vit-base-patch32"
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        
        # 检查模型是否已下载
        model_path = cache_dir / f"models--{model_name.replace('/', '--')}"
        if model_path.exists():
            models_info['aesthetic']['downloaded'] = True
            models_info['aesthetic']['model_name'] = model_name
            models_info['aesthetic']['model_path'] = str(model_path)
            
            # 计算模型大小
            total_size = 0
            for file_path in model_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            models_info['aesthetic']['size'] = f"{total_size / 1024**2:.2f} MB"
        
        models_info['aesthetic']['available'] = True
    except ImportError:
        pass
    
    return models_info


def get_memory_info() -> Dict[str, Any]:
    """获取内存信息"""
    memory_info = {
        'total': None,
        'available': None,
        'used': None
    }
    
    try:
        import psutil
        mem = psutil.virtual_memory()
        memory_info['total'] = f"{mem.total / 1024**3:.2f} GB"
        memory_info['available'] = f"{mem.available / 1024**3:.2f} GB"
        memory_info['used'] = f"{mem.used / 1024**3:.2f} GB"
        memory_info['percent'] = mem.percent
    except ImportError:
        pass
    
    return memory_info

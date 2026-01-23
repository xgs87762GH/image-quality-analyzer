"""ExifTool 测试"""
import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.exiftool_manager import ExifToolManager
from metadata.metadata_reader import MetadataReader


def test_exiftool():
    """测试 ExifTool"""
    manager = ExifToolManager()
    reader = MetadataReader()
    
    print(f"ExifTool 路径: {manager.get_exiftool_path()}")
    print(f"可用: {manager.is_available()}")
    print(f"MetadataReader 可用: {reader.is_available()}")
    
    if manager.is_available():
        import subprocess
        result = subprocess.run(
            [manager.get_exiftool_path(), "-ver"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(manager.exiftool_dir),
            stdin=subprocess.DEVNULL
        )
        if result.returncode == 0:
            print(f"版本: {result.stdout.strip()}")
        else:
            print(f"错误: {result.stderr}")


if __name__ == "__main__":
    test_exiftool()

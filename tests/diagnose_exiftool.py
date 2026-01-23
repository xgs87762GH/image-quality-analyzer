"""诊断 ExifTool 无法运行的问题"""
import sys
import io
import subprocess
from pathlib import Path

# 设置标准输出编码为 UTF-8（Windows）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.exiftool_manager import ExifToolManager


def diagnose_exiftool():
    """诊断 ExifTool 问题"""
    print("=" * 60)
    print("ExifTool 诊断工具")
    print("=" * 60)
    
    manager = ExifToolManager()
    exe_path = manager.get_exiftool_path()
    
    if not exe_path:
        print("[ERROR] ExifTool 路径未找到")
        return
    
    exe_path = Path(exe_path)
    exiftool_dir = manager.exiftool_dir
    
    print(f"\n1. 文件检查:")
    print(f"   可执行文件路径: {exe_path}")
    print(f"   文件存在: {exe_path.exists()}")
    if exe_path.exists():
        print(f"   文件大小: {exe_path.stat().st_size:,} bytes")
        print(f"   文件权限: {oct(exe_path.stat().st_mode)}")
    
    print(f"\n2. 目录检查:")
    print(f"   ExifTool 目录: {exiftool_dir}")
    print(f"   目录存在: {exiftool_dir.exists()}")
    
    exiftool_files_dir = exiftool_dir / "exiftool_files"
    print(f"   exiftool_files 目录: {exiftool_files_dir}")
    print(f"   目录存在: {exiftool_files_dir.exists()}")
    
    if exiftool_files_dir.exists():
        dll_files = list(exiftool_files_dir.glob("*.dll"))
        print(f"   DLL 文件数量: {len(dll_files)}")
        if dll_files:
            print(f"   前5个DLL文件:")
            for dll in dll_files[:5]:
                print(f"     - {dll.name}")
    
    print(f"\n3. 运行测试:")
    print(f"   工作目录: {exiftool_dir}")
    print(f"   命令: {exe_path.absolute()} -ver")
    
    try:
        result = subprocess.run(
            [str(exe_path.absolute()), '-ver'],
            capture_output=True,
            text=True,
            timeout=10,  # 增加超时时间
            cwd=str(exiftool_dir),
            stdin=subprocess.DEVNULL  # 避免等待输入（处理 "press ENTER" 提示）
        )
        
        print(f"   返回码: {result.returncode}")
        print(f"   标准输出: {result.stdout.strip() if result.stdout else '(空)'}")
        if result.stderr:
            print(f"   标准错误: {result.stderr.strip()}")
        
        if result.returncode == 0:
            print(f"   [OK] ExifTool 可以正常运行！")
        else:
            print(f"   [ERROR] ExifTool 运行失败（返回码: {result.returncode}）")
            
    except FileNotFoundError:
        print(f"   [ERROR] 文件未找到")
    except subprocess.TimeoutExpired:
        print(f"   [ERROR] 运行超时")
    except Exception as e:
        print(f"   [ERROR] 运行异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n4. Manager 状态检查:")
    print(f"   is_available(): {manager.is_available()}")
    print(f"   _has_executable(): {manager._has_executable()}")
    print(f"   _is_incomplete(): {manager._is_incomplete()}")
    
    print(f"\n5. 解决方案建议:")
    if not exe_path.exists():
        print("   - 文件不存在，请重新解压压缩包")
    elif not exiftool_files_dir.exists():
        print("   - 缺少 exiftool_files 目录，请重新解压完整的压缩包")
    elif manager._is_incomplete():
        print("   - 安装不完整，请删除 exiftool 目录中的文件，重新放入压缩包并解压")
    elif not manager.is_available():
        print("   - ExifTool 文件存在但无法运行，可能原因：")
        print("     1. 文件损坏 - 请重新下载压缩包")
        print("     2. 权限问题 - 尝试以管理员权限运行")
        print("     3. 防病毒软件阻止 - 检查防病毒软件设置")
        print("     4. DLL 依赖问题 - 确保 exiftool_files 目录完整")
    else:
        print("   - ExifTool 应该可以正常使用")


if __name__ == "__main__":
    diagnose_exiftool()

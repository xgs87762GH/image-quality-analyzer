"""数据库迁移模块"""
# 注意：由于Python模块名不能以数字开头，使用动态导入
import importlib.util
from pathlib import Path

def load_migration(module_name, file_path):
    """动态加载迁移模块"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_migrations(db):
    """运行所有迁移"""
    migrations_dir = Path(__file__).parent
    
    # 定义所有迁移文件
    migration_files = [
        ('002_add_thumbnail_and_deleted', migrations_dir / '002_add_thumbnail_and_deleted.py'),
        ('003_add_original_path', migrations_dir / '003_add_original_path.py'),
        ('004_add_ai_analysis_fields', migrations_dir / '004_add_ai_analysis_fields.py'),
        ('005_add_evaluations_array', migrations_dir / '005_add_evaluations_array.py'),
    ]
    
    for name, file_path in migration_files:
        if not file_path.exists():
            print(f"警告: 迁移文件 {file_path} 不存在，跳过")
            continue
            
        try:
            print(f"执行迁移 {name}...")
            migration = load_migration(name, file_path)
            migration.up(db)
        except Exception as e:
            error_str = str(e).lower()
            if "duplicate column" in error_str or "already exists" in error_str:
                print(f"迁移 {name} 已存在，跳过")
            else:
                print(f"迁移 {name} 失败: {e}")
                import traceback
                traceback.print_exc()

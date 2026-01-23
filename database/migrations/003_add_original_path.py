"""添加原路径字段的迁移"""
from database.connection import DatabaseConnection


def up(db: DatabaseConnection):
    """执行迁移"""
    conn = db.get_connection()
    
    # 添加original_path字段（如果不存在）
    try:
        conn.execute("ALTER TABLE images ADD COLUMN original_path TEXT")
        print("已添加 original_path 字段")
    except Exception as e:
        if "duplicate column" not in str(e).lower():
            print(f"添加 original_path 字段时出错: {e}")
    
    # 对于现有记录，将file_path复制到original_path
    try:
        conn.execute("""
            UPDATE images 
            SET original_path = file_path 
            WHERE original_path IS NULL
        """)
        print("已更新现有记录的 original_path")
    except Exception as e:
        print(f"更新 original_path 时出错: {e}")
    
    conn.commit()
    print("迁移完成")


def down(db: DatabaseConnection):
    """回滚迁移（SQLite不支持删除列）"""
    print("SQLite不支持删除列，无法回滚 original_path 字段")

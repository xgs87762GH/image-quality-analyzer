"""添加删除字段的迁移"""
from database.connection import DatabaseConnection


def up(db: DatabaseConnection):
    """执行迁移"""
    conn = db.get_connection()
    
    # 添加deleted_at字段（如果不存在）
    try:
        conn.execute("ALTER TABLE images ADD COLUMN deleted_at TIMESTAMP")
        print("已添加 deleted_at 字段")
    except Exception as e:
        if "duplicate column" not in str(e).lower():
            print(f"添加 deleted_at 字段时出错: {e}")
    
    # 创建索引
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_deleted_at ON images(deleted_at)")
        print("已创建 deleted_at 索引")
    except Exception as e:
        print(f"创建索引时出错: {e}")
    
    conn.commit()
    print("迁移完成")


def down(db: DatabaseConnection):
    """回滚迁移（SQLite不支持删除列，这里只删除索引）"""
    conn = db.get_connection()
    try:
        conn.execute("DROP INDEX IF EXISTS idx_deleted_at")
        print("已删除 deleted_at 索引")
    except Exception:
        pass
    conn.commit()

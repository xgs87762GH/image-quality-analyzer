"""添加AI分析结果和评估结果字段的迁移"""
from database.connection import DatabaseConnection


def up(db: DatabaseConnection):
    """执行迁移"""
    conn = db.get_connection()
    
    # 在metadata表中添加AI分析相关字段
    try:
        conn.execute("ALTER TABLE metadata ADD COLUMN ai_analysis TEXT")
        print("已添加 ai_analysis 字段")
    except Exception as e:
        if "duplicate column" not in str(e).lower():
            print(f"添加 ai_analysis 字段时出错: {e}")
    
    try:
        conn.execute("ALTER TABLE metadata ADD COLUMN evaluation_keyword TEXT")
        print("已添加 evaluation_keyword 字段")
    except Exception as e:
        if "duplicate column" not in str(e).lower():
            print(f"添加 evaluation_keyword 字段时出错: {e}")
    
    try:
        conn.execute("ALTER TABLE metadata ADD COLUMN evaluation_result TEXT")
        print("已添加 evaluation_result 字段")
    except Exception as e:
        if "duplicate column" not in str(e).lower():
            print(f"添加 evaluation_result 字段时出错: {e}")
    
    conn.commit()
    print("迁移完成")


def down(db: DatabaseConnection):
    """回滚迁移（SQLite不支持删除列）"""
    print("SQLite不支持删除列，无法回滚这些字段")

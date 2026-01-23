"""添加评估问题数组字段的迁移（替换单个评估问题字段）"""
from database.connection import DatabaseConnection
import json


def up(db: DatabaseConnection):
    """执行迁移"""
    conn = db.get_connection()
    
    # 添加新的evaluations字段（JSON格式，存储多个评估问题）
    try:
        conn.execute("ALTER TABLE metadata ADD COLUMN evaluations TEXT")
        print("已添加 evaluations 字段")
    except Exception as e:
        if "duplicate column" not in str(e).lower():
            print(f"添加 evaluations 字段时出错: {e}")
    
    # 迁移旧数据：将evaluation_keyword和evaluation_result合并为evaluations数组
    try:
        cursor = conn.execute("""
            SELECT id, evaluation_keyword, evaluation_result 
            FROM metadata 
            WHERE evaluation_keyword IS NOT NULL AND evaluation_keyword != ''
        """)
        
        rows = cursor.fetchall()
        migrated_count = 0
        
        for row in rows:
            keyword = row['evaluation_keyword']
            result = row.get('evaluation_result')
            
            if keyword:
                # 创建评估问题数组
                evaluations = [{
                    'keyword': keyword,
                    'result': result if result else None
                }]
                
                # 更新记录
                conn.execute("""
                    UPDATE metadata 
                    SET evaluations = ? 
                    WHERE id = ?
                """, (json.dumps(evaluations, ensure_ascii=False), row['id']))
                migrated_count += 1
        
        if migrated_count > 0:
            print(f"已迁移 {migrated_count} 条旧数据到 evaluations 字段")
        else:
            print("没有需要迁移的数据")
            
    except Exception as e:
        print(f"迁移旧数据时出错: {e}")
    
    conn.commit()
    print("迁移完成")


def down(db: DatabaseConnection):
    """回滚迁移（SQLite不支持删除列）"""
    print("SQLite不支持删除列，无法回滚 evaluations 字段")
    print("注意：evaluation_keyword 和 evaluation_result 字段仍然保留以保持向后兼容")

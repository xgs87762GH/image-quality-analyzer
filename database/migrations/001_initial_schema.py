"""初始数据库架构迁移"""
from database.connection import DatabaseConnection
from database.models import create_tables


def up(db: DatabaseConnection):
    """执行迁移"""
    create_tables(db)
    print("数据库表已创建")


def down(db: DatabaseConnection):
    """回滚迁移"""
    db.execute("DROP TABLE IF EXISTS metadata")
    db.execute("DROP TABLE IF EXISTS quality_assessments")
    db.execute("DROP TABLE IF EXISTS images")
    db.get_connection().commit()
    print("数据库表已删除")

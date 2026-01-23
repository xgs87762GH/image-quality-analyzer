"""数据库连接管理"""
import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional
from pathlib import Path

from config.settings import get_settings


class DatabaseConnection:
    """数据库连接管理器"""
    
    _local = threading.local()
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径，如果为None则使用配置中的路径
        """
        settings = get_settings()
        self.db_path = db_path or settings.database.db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """确保数据库文件存在"""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        if not db_file.exists():
            # 创建空数据库文件
            conn = sqlite3.connect(self.db_path)
            conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接（线程安全）
        
        Returns:
            SQLite连接对象
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            settings = get_settings()
            self._local.connection = sqlite3.connect(
                self.db_path,
                timeout=settings.database.timeout,
                check_same_thread=settings.database.check_same_thread
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def close(self):
        """关闭连接"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """执行SQL查询"""
        conn = self.get_connection()
        return conn.execute(query, params)
    
    def executemany(self, query: str, params_list: list) -> sqlite3.Cursor:
        """批量执行SQL查询"""
        conn = self.get_connection()
        return conn.executemany(query, params_list)


# 全局数据库连接实例
_db: Optional[DatabaseConnection] = None


def get_db() -> DatabaseConnection:
    """获取全局数据库连接实例"""
    global _db
    if _db is None:
        _db = DatabaseConnection()
    return _db


def init_database():
    """初始化数据库（创建表并运行迁移）"""
    from database.models import create_tables
    db = get_db()
    create_tables(db)
    db.get_connection().commit()
    
    # 运行数据库迁移
    try:
        from database.migrations import run_migrations
        run_migrations(db)
    except Exception as e:
        print(f"警告: 数据库迁移执行失败: {e}")
        import traceback
        traceback.print_exc()
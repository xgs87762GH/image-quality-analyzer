"""数据库连接管理"""
import sqlite3
import threading
import time
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
            # 添加重试机制处理 I/O 错误
            max_retries = 3
            retry_delay = 0.1
            
            for attempt in range(max_retries):
                try:
                    self._local.connection = sqlite3.connect(
                        self.db_path,
                        timeout=settings.database.timeout,
                        check_same_thread=settings.database.check_same_thread
                    )
                    self._local.connection.row_factory = sqlite3.Row
                    
                    # 禁用 WAL 模式，使用默认的 DELETE 模式，避免 I/O 错误和数据库损坏
                    # WAL 模式在某些文件系统（网络文件系统、FAT32等）上不支持，会导致 disk I/O error
                    # 如果数据库之前被设置为 WAL 模式但失败，尝试切换回 DELETE 模式
                    try:
                        cursor = self._local.connection.execute('PRAGMA journal_mode')
                        current_mode = cursor.fetchone()
                        if current_mode and current_mode[0] == 'wal':
                            # 如果当前是 WAL 模式，尝试切换回 DELETE 模式
                            try:
                                cursor = self._local.connection.execute('PRAGMA journal_mode=DELETE')
                                result = cursor.fetchone()
                                from utils.logger import get_logger
                                logger = get_logger()
                                logger.info(f"已从 WAL 模式切换回 DELETE 模式: {result[0] if result else 'unknown'}")
                            except Exception as e:
                                # 切换失败，记录但不影响使用
                                from utils.logger import get_logger
                                logger = get_logger()
                                logger.warning(f"无法切换日志模式: {e}")
                    except Exception:
                        # 查询当前模式失败，忽略（可能是数据库损坏，后续会处理）
                        pass
                    
                    # 设置其他优化参数（这些通常不会失败）
                    try:
                        self._local.connection.execute('PRAGMA synchronous=NORMAL')
                        self._local.connection.execute('PRAGMA cache_size=10000')
                        self._local.connection.execute('PRAGMA temp_store=MEMORY')
                    except:
                        pass  # 忽略设置失败
                    return self._local.connection
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        # 如果连接存在但有问题，关闭它
                        if hasattr(self._local, 'connection') and self._local.connection:
                            try:
                                self._local.connection.close()
                            except:
                                pass
                            self._local.connection = None
                        continue
                    else:
                        # 最后一次尝试失败，记录错误并重新抛出
                        from utils.logger import get_logger
                        logger = get_logger()
                        logger.error(f"数据库连接失败 (尝试 {max_retries} 次): {e}")
                        raise
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
        """执行SQL查询（带重试机制）"""
        max_retries = 5  # 增加重试次数
        retry_delay = 0.2  # 增加重试延迟
        
        for attempt in range(max_retries):
            try:
                conn = self.get_connection()
                # 检查连接是否有效
                try:
                    conn.execute('SELECT 1')
                except:
                    # 连接无效，关闭并重新创建
                    if hasattr(self._local, 'connection') and self._local.connection:
                        try:
                            self._local.connection.close()
                        except:
                            pass
                        self._local.connection = None
                    conn = self.get_connection()
                
                return conn.execute(query, params)
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                error_msg = str(e).lower()
                # 如果是 I/O 错误或锁定错误，尝试重试
                if ('disk i/o' in error_msg or 'locked' in error_msg or 
                    'database is locked' in error_msg or 'unable to open' in error_msg) and attempt < max_retries - 1:
                    # 关闭当前连接，下次调用 get_connection 时会重新创建
                    if hasattr(self._local, 'connection') and self._local.connection:
                        try:
                            self._local.connection.close()
                        except:
                            pass
                        self._local.connection = None
                    # 指数退避
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                else:
                    # 其他错误或重试次数用完，记录并抛出
                    from utils.logger import get_logger
                    logger = get_logger()
                    logger.error(f"数据库查询失败 (尝试 {attempt + 1}/{max_retries}): {e}, 查询: {query[:100]}")
                    raise
    
    def executemany(self, query: str, params_list: list) -> sqlite3.Cursor:
        """批量执行SQL查询（带重试机制）"""
        max_retries = 5  # 增加重试次数
        retry_delay = 0.2  # 增加重试延迟
        
        for attempt in range(max_retries):
            try:
                conn = self.get_connection()
                # 检查连接是否有效
                try:
                    conn.execute('SELECT 1')
                except:
                    # 连接无效，关闭并重新创建
                    if hasattr(self._local, 'connection') and self._local.connection:
                        try:
                            self._local.connection.close()
                        except:
                            pass
                        self._local.connection = None
                    conn = self.get_connection()
                
                return conn.executemany(query, params_list)
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                error_msg = str(e).lower()
                # 如果是 I/O 错误或锁定错误，尝试重试
                if ('disk i/o' in error_msg or 'locked' in error_msg or 
                    'database is locked' in error_msg or 'unable to open' in error_msg) and attempt < max_retries - 1:
                    # 关闭当前连接，下次调用 get_connection 时会重新创建
                    if hasattr(self._local, 'connection') and self._local.connection:
                        try:
                            self._local.connection.close()
                        except:
                            pass
                        self._local.connection = None
                    # 指数退避
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                else:
                    # 其他错误或重试次数用完，记录并抛出
                    from utils.logger import get_logger
                    logger = get_logger()
                    logger.error(f"数据库批量查询失败 (尝试 {attempt + 1}/{max_retries}): {e}, 查询: {query[:100]}")
                    raise


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
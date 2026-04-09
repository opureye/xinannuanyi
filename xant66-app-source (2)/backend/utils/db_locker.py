"""
数据库连接池和锁机制模块
提供线程安全的数据库连接管理和锁功能
"""
import sqlite3
import threading
import time
import logging
import queue
from contextlib import contextmanager
from typing import Optional, Generator
from functools import wraps

logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """数据库连接池"""
    
    def __init__(self, db_path: str, pool_size: int = 5, timeout: float = 5.0):
        """
        初始化连接池
        
        Args:
            db_path: 数据库路径
            pool_size: 连接池大小
            timeout: 获取连接的超时时间（秒）
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.timeout = timeout
        self._pool = queue.Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._created_connections = 0
        
        # 预创建连接
        self._initialize_pool()
    
    def _initialize_pool(self):
        """初始化连接池"""
        success_count = 0
        for _ in range(self.pool_size):
            conn = self._create_connection()
            if conn:
                self._pool.put(conn)
                success_count += 1
        
        if success_count == 0:
            logger.error(f"连接池初始化失败：无法创建任何数据库连接（数据库路径：{self.db_path}）")
            raise RuntimeError(f"无法初始化数据库连接池：无法创建任何连接到数据库 {self.db_path}")
        elif success_count < self.pool_size:
            logger.warning(f"连接池部分初始化：成功创建 {success_count}/{self.pool_size} 个连接")
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """创建新的数据库连接"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=self.timeout, check_same_thread=False)
            # 启用外键约束
            conn.execute("PRAGMA foreign_keys = ON")
            # 设置WAL模式以提高并发性能
            conn.execute("PRAGMA journal_mode = WAL")
            # 设置同步模式为NORMAL（性能与安全性的平衡）
            conn.execute("PRAGMA synchronous = NORMAL")
            # 设置缓存大小
            conn.execute("PRAGMA cache_size = -64000")  # 64MB缓存
            self._created_connections += 1
            logger.debug(f"创建数据库连接 #{self._created_connections}")
            return conn
        except sqlite3.Error as e:
            logger.error(f"创建数据库连接失败: {e}")
            return None
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        从连接池获取连接（上下文管理器）
        
        Usage:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
        """
        conn = None
        try:
            # 尝试从池中获取连接，如果超时则创建新连接
            try:
                conn = self._pool.get(timeout=self.timeout)
            except queue.Empty:
                logger.warning("连接池已满，创建临时连接")
                conn = self._create_connection()
                if not conn:
                    raise RuntimeError("无法创建数据库连接")
            
            yield conn
            
        except Exception as e:
            # 如果发生错误，关闭连接而不是归还到池中
            if conn:
                try:
                    conn.close()
                except:
                    pass
                # 如果是从池中获取的连接，需要创建一个新连接补充
                if self._pool.qsize() < self.pool_size:
                    new_conn = self._create_connection()
                    if new_conn:
                        self._pool.put(new_conn)
            raise
        else:
            # 成功执行，归还连接
            try:
                self._pool.put(conn, block=False)
            except queue.Full:
                # 池已满，关闭连接
                conn.close()
    
    def close_all(self):
        """关闭所有连接"""
        with self._lock:
            while not self._pool.empty():
                try:
                    conn = self._pool.get_nowait()
                    conn.close()
                except queue.Empty:
                    break
            logger.info("连接池已关闭")


class DatabaseLock:
    """数据库锁管理器"""
    
    def __init__(self):
        """初始化锁管理器"""
        self._locks = {}
        self._global_lock = threading.Lock()
        self._read_locks = {}  # 读锁计数器
        self._write_locks = {}  # 写锁
        self._lock_manager = threading.Lock()
    
    @contextmanager
    def read_lock(self, table: str, timeout: float = 10.0):
        """
        获取读锁（共享锁）
        
        Args:
            table: 表名
            timeout: 超时时间（秒）
        """
        start_time = time.time()
        
        with self._lock_manager:
            # 检查是否有写锁
            while table in self._write_locks:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    raise RuntimeError(f"获取读锁超时: {table}")
                time.sleep(0.01)  # 短暂等待
            
            # 增加读锁计数
            if table not in self._read_locks:
                self._read_locks[table] = 0
            self._read_locks[table] += 1
        
        try:
            yield
        finally:
            with self._lock_manager:
                if table in self._read_locks:
                    self._read_locks[table] -= 1
                    if self._read_locks[table] <= 0:
                        del self._read_locks[table]
    
    @contextmanager
    def write_lock(self, table: str, timeout: float = 10.0):
        """
        获取写锁（排他锁）
        
        Args:
            table: 表名
            timeout: 超时时间（秒）
        """
        start_time = time.time()
        
        with self._lock_manager:
            # 检查是否有读锁或写锁
            while table in self._read_locks or table in self._write_locks:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    raise RuntimeError(f"获取写锁超时: {table}")
                time.sleep(0.01)  # 短暂等待
            
            # 设置写锁
            self._write_locks[table] = threading.current_thread().ident
        
        try:
            yield
        finally:
            with self._lock_manager:
                if table in self._write_locks:
                    del self._write_locks[table]
    
    @contextmanager
    def transaction_lock(self, tables: list, timeout: float = 30.0):
        """
        获取事务锁（多个表的写锁）
        
        Args:
            tables: 表名列表
            timeout: 超时时间（秒）
        """
        start_time = time.time()
        locked_tables = []
        
        try:
            # 按表名排序以避免死锁
            sorted_tables = sorted(set(tables))
            
            for table in sorted_tables:
                with self._lock_manager:
                    # 检查是否有读锁或写锁
                    while table in self._read_locks or table in self._write_locks:
                        elapsed = time.time() - start_time
                        if elapsed > timeout:
                            # 释放已获取的锁
                            for locked_table in locked_tables:
                                if locked_table in self._write_locks:
                                    del self._write_locks[locked_table]
                            raise RuntimeError(f"获取事务锁超时: {table}")
                        time.sleep(0.01)
                    
                    # 设置写锁
                    self._write_locks[table] = threading.current_thread().ident
                    locked_tables.append(table)
            
            yield
            
        finally:
            # 释放所有锁
            with self._lock_manager:
                for table in locked_tables:
                    if table in self._write_locks:
                        del self._write_locks[table]


def with_db_lock(lock_type: str = "write", tables: list = None, timeout: float = 10.0):
    """
    装饰器：为函数添加数据库锁
    
    Args:
        lock_type: 锁类型（"read"或"write"）
        tables: 表名列表（如果为None，则从函数参数中获取）
        timeout: 超时时间（秒）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 如果表名列表为None，尝试从kwargs中获取
            lock_tables = tables if tables is not None else kwargs.get('tables', [])
            
            if not lock_tables:
                # 如果没有指定表，创建一个全局锁
                lock_manager = DatabaseLock()
                if lock_type == "read":
                    with lock_manager.read_lock("global", timeout):
                        return func(*args, **kwargs)
                else:
                    with lock_manager.write_lock("global", timeout):
                        return func(*args, **kwargs)
            else:
                lock_manager = DatabaseLock()
                if lock_type == "read":
                    # 读锁可以并发
                    with lock_manager.read_lock(lock_tables[0], timeout):
                        return func(*args, **kwargs)
                else:
                    # 写锁需要获取所有表的锁
                    with lock_manager.transaction_lock(lock_tables, timeout):
                        return func(*args, **kwargs)
        
        return wrapper
    return decorator


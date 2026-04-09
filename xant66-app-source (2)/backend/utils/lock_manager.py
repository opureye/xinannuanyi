import sqlite3
import os
from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, Optional

# Python 3.11+ 有 datetime.UTC；为兼容 Python 3.10 这里统一使用 timezone.utc
UTC = timezone.utc

logger = logging.getLogger('lock_manager')

class LockManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_lock_table_exists()
        logger.info(f"[lock_manager] 初始化锁管理器，使用的数据库路径: {os.path.abspath(self.db_path)}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def _ensure_lock_table_exists(self):
        """
        确保锁表存在
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_locks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lock_name TEXT UNIQUE NOT NULL,
                    locked_by TEXT NOT NULL,
                    locked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    lock_status TEXT NOT NULL DEFAULT 'active'
                )
                ''')
                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_locks_lock_name ON audit_locks(lock_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_locks_expires_at ON audit_locks(expires_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_locks_lock_status ON audit_locks(lock_status)')
                conn.commit()
                logger.info("[lock_manager] 锁表初始化成功")
        except Exception as e:
            logger.error(f"[lock_manager] 创建锁表失败: {str(e)}")
    
    def get_lock(self, lock_name: str, locked_by: str, lock_duration: int = 300) -> bool:
        """
        获取锁
        
        :param lock_name: 锁名称
        :param locked_by: 锁定者的用户名
        :param lock_duration: 锁持续时间（秒），默认5分钟
        :return: 是否成功获取锁
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 先清理过期的锁
                self._cleanup_expired_locks(conn)
                
                # 检查锁是否已经存在且有效
                cursor.execute(
                    "SELECT lock_status, locked_by FROM audit_locks WHERE lock_name = ? AND lock_status = 'active'",
                    (lock_name,)
                )
                existing_lock = cursor.fetchone()
                
                if existing_lock:
                    lock_status, current_locked_by = existing_lock
                    # 如果锁已经被当前用户持有，则允许继续操作（延长锁）
                    if current_locked_by == locked_by:
                        # 延长锁的有效期
                        now = datetime.now(UTC)
                        expires_at = now + timedelta(seconds=lock_duration)
                        cursor.execute(
                            "UPDATE audit_locks SET expires_at = ? WHERE lock_name = ? AND locked_by = ? AND lock_status = 'active'",
                            (expires_at.strftime('%Y-%m-%d %H:%M:%S'), lock_name, locked_by)
                        )
                        conn.commit()
                        logger.info(f"[lock_manager] 用户 {locked_by} 延长了锁 {lock_name} 的有效期")
                        return True
                    else:
                        logger.info(f"[lock_manager] 锁 {lock_name} 已被用户 {current_locked_by} 占用")
                        return False
                
                # 计算过期时间（使用UTC时间）
                now = datetime.now(UTC)
                expires_at = now + timedelta(seconds=lock_duration)
                
                # 插入新锁
                cursor.execute(
                    "INSERT OR REPLACE INTO audit_locks (lock_name, locked_by, locked_at, expires_at, lock_status) VALUES (?, ?, ?, ?, ?)",
                    (lock_name, locked_by, now.strftime('%Y-%m-%d %H:%M:%S'), expires_at.strftime('%Y-%m-%d %H:%M:%S'), 'active')
                )
                conn.commit()
                
                logger.info(f"[lock_manager] 用户 {locked_by} 成功获取锁 {lock_name}")
                return True
                
        except Exception as e:
            logger.error(f"[lock_manager] 获取锁 {lock_name} 失败: {str(e)}")
            return False
    
    def release_lock(self, lock_name: str, locked_by: str) -> bool:
        """
        释放锁
        
        :param lock_name: 锁名称
        :param locked_by: 锁定者的用户名
        :return: 是否成功释放锁
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 只有锁的持有者才能释放锁
                cursor.execute(
                    "UPDATE audit_locks SET lock_status = 'expired' WHERE lock_name = ? AND locked_by = ? AND lock_status = 'active'",
                    (lock_name, locked_by)
                )
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"[lock_manager] 用户 {locked_by} 成功释放锁 {lock_name}")
                    return True
                else:
                    logger.warning(f"[lock_manager] 用户 {locked_by} 尝试释放不属于自己的锁 {lock_name} 或锁不存在")
                    return False
                    
        except Exception as e:
            logger.error(f"[lock_manager] 释放锁 {lock_name} 失败: {str(e)}")
            return False
    
    def force_release_lock(self, lock_name: str) -> bool:
        """
        强制释放锁（管理员使用）
        
        :param lock_name: 锁名称
        :return: 是否成功释放锁
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "UPDATE audit_locks SET lock_status = 'expired' WHERE lock_name = ? AND lock_status = 'active'",
                    (lock_name,)
                )
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"[lock_manager] 锁 {lock_name} 被强制释放")
                    return True
                else:
                    logger.warning(f"[lock_manager] 尝试强制释放不存在的锁 {lock_name}")
                    return False
                    
        except Exception as e:
            logger.error(f"[lock_manager] 强制释放锁 {lock_name} 失败: {str(e)}")
            return False
    
    def check_lock(self, lock_name: str) -> Optional[Dict[str, any]]:
        """
        检查锁的状态
        
        :param lock_name: 锁名称
        :return: 锁信息，如果锁不存在或已过期则返回None
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 先清理过期的锁
                self._cleanup_expired_locks(conn)
                
                # 检查锁是否存在且有效
                cursor.execute(
                    "SELECT * FROM audit_locks WHERE lock_name = ? AND lock_status = 'active'",
                    (lock_name,)
                )
                lock = cursor.fetchone()
                
                if lock:
                    return dict(lock)
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"[lock_manager] 检查锁 {lock_name} 状态失败: {str(e)}")
            return None
    
    def _cleanup_expired_locks(self, conn: sqlite3.Connection):
        """
        清理过期的锁
        
        :param conn: 数据库连接
        """
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE audit_locks SET lock_status = 'expired' WHERE expires_at < CURRENT_TIMESTAMP AND lock_status = 'active'"
            )
            if cursor.rowcount > 0:
                logger.info(f"[lock_manager] 清理了 {cursor.rowcount} 个过期锁")
        except Exception as e:
            logger.error(f"[lock_manager] 清理过期锁失败: {str(e)}")
            # 不回滚，继续执行后续操作
    
    def extend_lock(self, lock_name: str, locked_by: str, additional_duration: int = 300) -> bool:
        """
        延长锁的有效期
        
        :param lock_name: 锁名称
        :param locked_by: 锁定者的用户名
        :param additional_duration: 延长的时间（秒），默认5分钟
        :return: 是否成功延长锁
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 只有锁的持有者才能延长锁
                cursor.execute(
                    "SELECT expires_at FROM audit_locks WHERE lock_name = ? AND locked_by = ? AND lock_status = 'active'",
                    (lock_name, locked_by)
                )
                existing_lock = cursor.fetchone()
                
                if not existing_lock:
                    logger.warning(f"[lock_manager] 用户 {locked_by} 尝试延长不属于自己的锁 {lock_name} 或锁不存在")
                    return False
                
                # 计算新的过期时间
                current_expires = datetime.strptime(existing_lock[0], '%Y-%m-%d %H:%M:%S')
                new_expires = current_expires + timedelta(seconds=additional_duration)
                
                cursor.execute(
                    "UPDATE audit_locks SET expires_at = ? WHERE lock_name = ? AND locked_by = ? AND lock_status = 'active'",
                    (new_expires.strftime('%Y-%m-%d %H:%M:%S'), lock_name, locked_by)
                )
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"[lock_manager] 用户 {locked_by} 成功延长锁 {lock_name} 有效期至 {new_expires}")
                    return True
                else:
                    return False
                    
        except Exception as e:
            logger.error(f"[lock_manager] 延长锁 {lock_name} 有效期失败: {str(e)}")
            return False

# 创建锁管理器实例
from backend.config import settings
lock_manager = LockManager(settings.db_path)

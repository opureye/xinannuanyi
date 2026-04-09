#!/usr/bin/env python3
"""
数据库锁监测和管理脚本

功能：
1. 显示所有活动锁
2. 显示所有锁历史记录
3. 强制释放特定锁
4. 清理过期锁
5. 检查特定锁的状态
"""

import os
import sys
import sqlite3
from datetime import datetime, UTC
import argparse

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from utils.lock_manager import LockManager

class LockMonitor:
    def __init__(self, db_path: str):
        """
        初始化锁监测器
        
        :param db_path: 数据库路径
        """
        self.db_path = db_path
        self.lock_manager = LockManager(db_path)
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接
        
        :return: sqlite3.Connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    
    def list_active_locks(self):
        """
        显示所有当前活动的锁
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 先清理过期锁
                cursor.execute(
                    "UPDATE audit_locks SET lock_status = 'expired' WHERE expires_at < CURRENT_TIMESTAMP AND lock_status = 'active'"
                )
                conn.commit()
                
                # 查询活动锁
                cursor.execute(
                    "SELECT * FROM audit_locks WHERE lock_status = 'active' ORDER BY locked_at DESC"
                )
                locks = cursor.fetchall()
                
                if not locks:
                    print("当前没有活动的锁")
                    return
                
                print("===== 活动锁列表 =====")
                print(f"{'锁名称':<25} {'锁定者':<20} {'锁定时间':<25} {'过期时间':<25} {'状态':<10}")
                print("-" * 105)
                
                for lock in locks:
                    lock_name = lock['lock_name']
                    locked_by = lock['locked_by']
                    locked_at = lock['locked_at']
                    expires_at = lock['expires_at']
                    lock_status = lock['lock_status']
                    
                    print(f"{lock_name:<25} {locked_by:<20} {locked_at:<25} {expires_at:<25} {lock_status:<10}")
                    
        except Exception as e:
            print(f"获取活动锁列表失败: {str(e)}")
    
    def list_all_locks(self):
        """
        显示所有锁历史记录
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 查询所有锁
                cursor.execute(
                    "SELECT * FROM audit_locks ORDER BY locked_at DESC"
                )
                locks = cursor.fetchall()
                
                if not locks:
                    print("锁历史记录为空")
                    return
                
                print("===== 所有锁历史记录 =====")
                print(f"{'ID':<5} {'锁名称':<25} {'锁定者':<20} {'锁定时间':<25} {'过期时间':<25} {'状态':<10}")
                print("-" * 110)
                
                for lock in locks:
                    lock_id = lock['id']
                    lock_name = lock['lock_name']
                    locked_by = lock['locked_by']
                    locked_at = lock['locked_at']
                    expires_at = lock['expires_at']
                    lock_status = lock['lock_status']
                    
                    print(f"{lock_id:<5} {lock_name:<25} {locked_by:<20} {locked_at:<25} {expires_at:<25} {lock_status:<10}")
                    
        except Exception as e:
            print(f"获取锁历史记录失败: {str(e)}")
    
    def force_release_lock(self, lock_name: str):
        """
        强制释放指定的锁
        
        :param lock_name: 锁名称
        """
        try:
            success = self.lock_manager.force_release_lock(lock_name)
            if success:
                print(f"成功：锁 '{lock_name}' 已被强制释放")
            else:
                print(f"警告：锁 '{lock_name}' 不存在或已过期")
        except Exception as e:
            print(f"强制释放锁 '{lock_name}' 失败: {str(e)}")
    
    def cleanup_expired_locks(self):
        """
        清理所有过期的锁
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 清理过期锁
                cursor.execute(
                    "UPDATE audit_locks SET lock_status = 'expired' WHERE expires_at < CURRENT_TIMESTAMP AND lock_status = 'active'"
                )
                count = cursor.rowcount
                conn.commit()
                
                if count > 0:
                    print(f"成功：清理了 {count} 个过期锁")
                else:
                    print("没有发现过期锁")
                    
        except Exception as e:
            print(f"清理过期锁失败: {str(e)}")
    
    def check_lock_status(self, lock_name: str):
        """
        检查特定锁的状态
        
        :param lock_name: 锁名称
        """
        try:
            lock_info = self.lock_manager.check_lock(lock_name)
            
            if lock_info:
                print(f"===== 锁 '{lock_name}' 的状态 =====")
                print(f"锁名称: {lock_info['lock_name']}")
                print(f"锁定者: {lock_info['locked_by']}")
                print(f"锁定时间: {lock_info['locked_at']}")
                print(f"过期时间: {lock_info['expires_at']}")
                print(f"状态: {lock_info['lock_status']}")
                
                # 检查是否过期（使用UTC时间）
                now = datetime.now(UTC)
                expires_at = datetime.strptime(lock_info['expires_at'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=UTC)
                if now > expires_at:
                    print(f"注意：该锁已于 {expires_at} UTC 过期")
                else:
                    remaining = expires_at - now
                    print(f"剩余有效时间: {remaining}")
                    print(f"本地时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)")
                    
            else:
                print(f"锁 '{lock_name}' 不存在或已过期")
                
        except Exception as e:
            print(f"检查锁 '{lock_name}' 状态失败: {str(e)}")

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='数据库锁监测和管理工具')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 列出活动锁
    list_active_parser = subparsers.add_parser('list', help='显示所有活动锁')
    
    # 列出所有锁
    list_all_parser = subparsers.add_parser('list-all', help='显示所有锁历史记录')
    
    # 强制释放锁
    release_parser = subparsers.add_parser('release', help='强制释放指定锁')
    release_parser.add_argument('lock_name', help='要释放的锁名称')
    
    # 清理过期锁
    cleanup_parser = subparsers.add_parser('cleanup', help='清理所有过期锁')
    
    # 检查锁状态
    check_parser = subparsers.add_parser('check', help='检查特定锁的状态')
    check_parser.add_argument('lock_name', help='要检查的锁名称')
    
    # 解析参数
    args = parser.parse_args()
    
    # 检查是否提供了命令
    if not args.command:
        parser.print_help()
        return
    
    # 获取数据库路径
    db_path = settings.db_path
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"错误：数据库文件不存在 - {db_path}")
        return
    
    # 初始化锁监测器
    monitor = LockMonitor(db_path)
    
    # 执行命令
    if args.command == 'list':
        monitor.list_active_locks()
    elif args.command == 'list-all':
        monitor.list_all_locks()
    elif args.command == 'release':
        monitor.force_release_lock(args.lock_name)
    elif args.command == 'cleanup':
        monitor.cleanup_expired_locks()
    elif args.command == 'check':
        monitor.check_lock_status(args.lock_name)
    
if __name__ == '__main__':
    main()

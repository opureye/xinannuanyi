#!/usr/bin/env python3
"""
测试数据库锁的时间处理
验证UTC时间是否正确使用，避免8小时时差问题
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta, UTC

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from utils.lock_manager import LockManager

def test_lock_time_handling():
    """测试锁的时间处理逻辑"""
    print("=== 测试数据库锁时间处理 ===")
    
    # 创建锁管理器实例
    lock_manager = LockManager(settings.db_path)
    
    # 测试锁名称
    test_lock_name = "test_time_lock"
    test_user = "test_user"
    lock_duration = 10  # 10秒锁
    
    try:
        # 1. 显示当前时间信息
        print(f"当前本地时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)")
        print(f"当前UTC时间: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 2. 获取测试锁
        print("1. 获取测试锁...")
        success = lock_manager.get_lock(test_lock_name, test_user, lock_duration)
        if success:
            print(f"   ✓ 成功获取锁: {test_lock_name}")
        else:
            print(f"   ✗ 获取锁失败: {test_lock_name}")
            return False
        
        # 3. 检查锁信息
        print("2. 检查锁信息...")
        lock_info = lock_manager.check_lock(test_lock_name)
        if lock_info:
            print(f"   ✓ 锁名称: {lock_info['lock_name']}")
            print(f"   ✓ 锁定者: {lock_info['locked_by']}")
            print(f"   ✓ 锁定时间: {lock_info['locked_at']}")
            print(f"   ✓ 过期时间: {lock_info['expires_at']}")
            print(f"   ✓ 锁状态: {lock_info['lock_status']}")
            
            # 验证时间戳格式
            try:
                locked_at_utc = datetime.strptime(lock_info['locked_at'], '%Y-%m-%d %H:%M:%S')
                expires_at_utc = datetime.strptime(lock_info['expires_at'], '%Y-%m-%d %H:%M:%S')
                
                # 计算持续时间
                duration = (expires_at_utc - locked_at_utc).total_seconds()
                print(f"   ✓ 锁持续时间: {duration}秒 (预期: {lock_duration}秒)")
                
                # 验证持续时间是否正确
                if abs(duration - lock_duration) < 1:
                    print("   ✓ 时间计算正确")
                else:
                    print(f"   ✗ 时间计算错误: 实际 {duration}秒, 预期 {lock_duration}秒")
                    return False
                    
            except ValueError as e:
                print(f"   ✗ 时间格式错误: {e}")
                return False
        else:
            print("   ✗ 未找到锁信息")
            return False
        
        print()
        
        # 4. 显示数据库中的原始数据
        print("3. 查看数据库原始数据...")
        conn = sqlite3.connect(settings.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_locks WHERE lock_name = ?", (test_lock_name,))
        db_lock = cursor.fetchone()
        if db_lock:
            print(f"   ✓ 数据库锁定时间: {db_lock['locked_at']}")
            print(f"   ✓ 数据库过期时间: {db_lock['expires_at']}")
        conn.close()
        
        print()
        
        # 5. 等待锁过期
        print("4. 等待锁过期...")
        wait_time = lock_duration + 2  # 等待时间超过锁的持续时间
        print(f"   等待 {wait_time} 秒...")
        import time
        time.sleep(wait_time)
        
        # 6. 检查锁是否已过期
        print("5. 检查锁是否已过期...")
        lock_info_after_expire = lock_manager.check_lock(test_lock_name)
        if not lock_info_after_expire:
            print("   ✓ 锁已正确过期")
        else:
            print(f"   ✗ 锁未过期: {lock_info_after_expire['lock_status']}")
            return False
        
        print()
        print("=== 测试完成: 所有时间处理正确! ===")
        return True
        
    finally:
        # 清理测试锁
        print("清理测试锁...")
        lock_manager.force_release_lock(test_lock_name)
        print("测试完成")

if __name__ == "__main__":
    test_lock_time_handling()

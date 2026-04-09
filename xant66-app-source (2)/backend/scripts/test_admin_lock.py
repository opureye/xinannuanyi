#!/usr/bin/env python3
"""
测试管理员锁管理功能
验证管理员可以重新获取自己锁定的功能
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from utils.lock_manager import LockManager

def test_admin_lock_management():
    """测试管理员锁管理逻辑"""
    print("=== 测试管理员锁管理功能 ===")
    
    # 创建锁管理器实例
    lock_manager = LockManager(settings.db_path)
    
    # 测试数据
    test_lock_name = "account_audit_lock"
    admin_user = "洪汉博"
    other_admin = "其他管理员"
    lock_duration = 30  # 30秒锁
    
    try:
        # 1. 显示当前时间
        print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 2. 第一个管理员获取锁
        print("1. 管理员洪汉博获取审计锁...")
        success = lock_manager.get_lock(test_lock_name, admin_user, lock_duration)
        if success:
            print(f"   ✓ 成功获取锁")
        else:
            print(f"   ✗ 获取锁失败")
            return False
        
        # 3. 同一个管理员再次获取锁（应该延长锁）
        print("2. 管理员洪汉博再次获取同一个锁（应该延长锁）...")
        success = lock_manager.get_lock(test_lock_name, admin_user, lock_duration)
        if success:
            print(f"   ✓ 成功延长锁有效期")
        else:
            print(f"   ✗ 延长锁失败")
            return False
        
        # 4. 另一个管理员尝试获取锁（应该失败）
        print("3. 其他管理员尝试获取同一个锁（应该失败）...")
        success = lock_manager.get_lock(test_lock_name, other_admin, lock_duration)
        if not success:
            print(f"   ✓ 正确拒绝了其他管理员的请求")
        else:
            print(f"   ✗ 不应该允许其他管理员获取锁")
            return False
        
        # 5. 第一个管理员释放锁
        print("4. 管理员洪汉博释放锁...")
        success = lock_manager.release_lock(test_lock_name, admin_user)
        if success:
            print(f"   ✓ 成功释放锁")
        else:
            print(f"   ✗ 释放锁失败")
            return False
        
        # 6. 再次获取锁验证锁已释放
        print("5. 验证锁已释放，其他管理员可以获取...")
        success = lock_manager.get_lock(test_lock_name, other_admin, lock_duration)
        if success:
            print(f"   ✓ 其他管理员成功获取锁")
        else:
            print(f"   ✗ 其他管理员无法获取锁")
            return False
        
        print()
        print("=== 测试完成: 管理员锁管理功能正常! ===")
        return True
        
    finally:
        # 清理测试锁
        print("清理测试锁...")
        lock_manager.force_release_lock(test_lock_name)
        print("测试完成")

if __name__ == "__main__":
    test_admin_lock_management()

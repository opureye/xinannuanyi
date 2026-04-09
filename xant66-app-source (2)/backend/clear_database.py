#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库清空脚本
用于清空论坛网站数据库中的所有表数据
"""

import sqlite3
import os
import sys

# 获取项目根目录
def get_project_root():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return current_dir

# 获取数据库路径
def get_database_path():
    return os.path.join(get_project_root(), 'database', 'forum.db')

# 确认操作
def confirm_action():
    """确认是否要执行清空数据库操作"""
    print("警告：此操作将清空数据库中的所有数据！")
    print("请确保您已经备份了重要数据。")
    print("\n数据库路径：", get_database_path())
    
    while True:
        response = input("\n您确定要继续吗？(y/n): ").lower()
        if response == 'y':
            return True
        elif response == 'n':
            return False
        else:
            print("请输入 y 或 n")

# 获取数据库中的所有表
def get_all_tables(conn):
    """获取数据库中的所有表名称"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [table[0] for table in cursor.fetchall()]
    cursor.close()
    return tables

# 清空数据库中的所有表
def clear_all_tables(conn):
    """清空数据库中的所有表数据"""
    try:
        # 获取所有表
        tables = get_all_tables(conn)
        
        if not tables:
            print("数据库中没有表")
            return True
        
        cursor = conn.cursor()
        
        # 关闭外键约束检查，否则可能会因为外键关联而无法删除数据
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        print(f"\n开始清空以下表：")
        for table in tables:
            print(f"  - {table}")
            cursor.execute(f"DELETE FROM {table}")
            print(f"    ✓ 表 {table} 已清空")
        
        # 重新开启外键约束检查
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # 提交事务
        conn.commit()
        
        print(f"\n✅ 成功清空所有表！")
        print(f"共清空了 {len(tables)} 个表")
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ 清空数据库时发生错误：{e}")
        conn.rollback()
        return False
    finally:
        cursor.close()

# 主函数
def main():
    """主函数"""
    print("=" * 50)
    print("论坛网站数据库清空工具")
    print("=" * 50)
    
    # 确认操作
    if not confirm_action():
        print("\n操作已取消")
        sys.exit(0)
    
    # 连接数据库
    db_path = get_database_path()
    
    try:
        conn = sqlite3.connect(db_path)
        print(f"\n✅ 成功连接到数据库：{db_path}")
        
        # 清空所有表
        success = clear_all_tables(conn)
        
        if success:
            print("\n🎉 操作完成！数据库已清空")
        else:
            print("\n❌ 操作失败！")
            sys.exit(1)
            
    except sqlite3.Error as e:
        print(f"\n❌ 连接数据库时发生错误：{e}")
        sys.exit(1)
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print(f"\n✓ 已断开数据库连接")

if __name__ == "__main__":
    main()

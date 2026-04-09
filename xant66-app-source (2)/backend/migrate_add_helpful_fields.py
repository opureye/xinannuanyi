#!/usr/bin/env python3
"""
数据库迁移脚本：为articles表添加helpful_count和unhelpful_count字段
"""
import sqlite3
import os
import sys

# 获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from backend.config import settings

def migrate_database():
    """
    执行数据库迁移
    """
    db_path = settings.db_path
    
    print(f"正在迁移数据库: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
        if not cursor.fetchone():
            print("错误: articles表不存在")
            return False
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(articles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'helpful_count' in columns and 'unhelpful_count' in columns:
            print("字段已存在，无需迁移")
            return True
        
        # 添加helpful_count字段
        if 'helpful_count' not in columns:
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN helpful_count INTEGER DEFAULT 0")
                print("✓ 已添加 helpful_count 字段")
            except sqlite3.OperationalError as e:
                print(f"✗ 添加 helpful_count 字段失败: {e}")
                return False
        else:
            print("✓ helpful_count 字段已存在")
        
        # 添加unhelpful_count字段
        if 'unhelpful_count' not in columns:
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN unhelpful_count INTEGER DEFAULT 0")
                print("✓ 已添加 unhelpful_count 字段")
            except sqlite3.OperationalError as e:
                print(f"✗ 添加 unhelpful_count 字段失败: {e}")
                return False
        else:
            print("✓ unhelpful_count 字段已存在")
        
        conn.commit()
        conn.close()
        
        print("数据库迁移完成！")
        return True
        
    except Exception as e:
        print(f"迁移失败: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)

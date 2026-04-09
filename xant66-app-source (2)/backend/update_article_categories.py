#!/usr/bin/env python3
"""
更新旧文章的分类名称
"""
import sqlite3
import os

# 数据库路径
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'forum.db')

# 分类名称映射
category_mapping = {
    "测试分类": "内科",
    "外科互助分享": "外科",
    "内科互助分享": "内科",
    "皮肤科互助分享": "皮肤科",
    "妇产科互助分享": "妇产科",
    "儿科互助分享": "儿科",
    "神经科互助分享": "神经科",
    "中医科互助分享": "中医科",
    "肿瘤科互助分享": "肿瘤科",
    "心理互助分享": "心理科",
    "互助打气，分享成功": "其他",
    "项目介绍": "其他"
}

def update_article_categories():
    """
    更新文章的分类名称
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查看当前所有分类
        cursor.execute("SELECT DISTINCT category FROM articles")
        current_categories = [row[0] for row in cursor.fetchall()]
        
        print("当前数据库中的分类:")
        for cat in current_categories:
            print(f"  - {cat}")
        
        print(f"\n开始更新分类名称...")
        
        updated_count = 0
        for old_category, new_category in category_mapping.items():
            # 检查是否存在旧分类
            cursor.execute("SELECT COUNT(*) FROM articles WHERE category = ?", (old_category,))
            count = cursor.fetchone()[0]
            
            if count > 0:
                # 更新分类名称
                cursor.execute(
                    "UPDATE articles SET category = ? WHERE category = ?",
                    (new_category, old_category)
                )
                updated_count += count
                print(f"  ✅ 将 {count} 篇文章从 '{old_category}' 更新为 '{new_category}'")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ 共更新了 {updated_count} 篇文章的分类名称")
        
        # 显示更新后的分类
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM articles")
        new_categories = [row[0] for row in cursor.fetchall()]
        
        print(f"\n更新后的分类:")
        for cat in new_categories:
            print(f"  - {cat}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 更新失败: {e}")

if __name__ == "__main__":
    print("=== 更新文章分类名称 ===")
    update_article_categories()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
from datetime import datetime

def add_test_articles():
    """添加测试文章数据"""
    
    # 数据库路径
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'forum.db')
    
    # 测试文章数据
    test_articles = [
        {
            'title': '欢迎来到我们的论坛',
            'content': '这是一个测试文章，用于展示论坛的文章功能。在这里，用户可以发布各种类型的文章，分享自己的想法和经验。我们的论坛支持多种分类，包括技术、生活、娱乐等。希望大家能够积极参与讨论，共同建设一个友好的社区环境。',
            'author': 'admin',
            'category': '公告',
            'status': 'approved'
        },
        {
            'title': 'Python编程入门指南',
            'content': 'Python是一种简单易学的编程语言，非常适合初学者。本文将介绍Python的基本语法、数据类型、控制结构等内容。Python具有简洁的语法和强大的功能，广泛应用于Web开发、数据分析、人工智能等领域。学习Python可以帮助你快速入门编程世界。',
            'author': 'tech_user',
            'category': '技术',
            'status': 'approved'
        },
        {
            'title': '健康生活小贴士',
            'content': '保持健康的生活方式对每个人都很重要。本文分享一些简单实用的健康小贴士：1. 保持规律的作息时间；2. 均衡饮食，多吃蔬菜水果；3. 适量运动，每天至少30分钟；4. 保持良好的心态；5. 定期体检。这些简单的习惯可以帮助我们拥有更健康的身体。',
            'author': 'health_expert',
            'category': '生活',
            'status': 'approved'
        },
        {
            'title': '电影推荐：经典科幻片',
            'content': '科幻电影一直是电影界的重要类型，它们不仅娱乐观众，还能启发我们对未来的思考。今天推荐几部经典的科幻电影：《银翼杀手》、《黑客帝国》、《星际穿越》、《阿凡达》等。这些电影都有着精彩的故事情节和震撼的视觉效果，值得一看。',
            'author': 'movie_lover',
            'category': '娱乐',
            'status': 'approved'
        },
        {
            'title': '学习方法分享',
            'content': '高效的学习方法可以帮助我们更好地掌握知识。这里分享一些实用的学习技巧：1. 制定明确的学习目标；2. 合理安排学习时间；3. 主动思考和总结；4. 多做练习和实践；5. 与他人交流讨论。记住，学习是一个持续的过程，需要耐心和坚持。',
            'author': 'study_master',
            'category': '教育',
            'status': 'approved'
        }
    ]
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查articles表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='articles'
        """)
        
        if not cursor.fetchone():
            print("articles表不存在，正在创建...")
            # 创建articles表
            cursor.execute("""
                CREATE TABLE articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    author TEXT NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    view_count INTEGER DEFAULT 0,
                    like_count INTEGER DEFAULT 0
                )
            """)
            print("articles表创建成功")
        
        # 清空现有的测试数据
        cursor.execute("DELETE FROM articles WHERE author IN ('admin', 'tech_user', 'health_expert', 'movie_lover', 'study_master')")
        
        # 插入测试文章
        for article in test_articles:
            cursor.execute("""
                INSERT INTO articles (title, content, author, category, status, created_at, view_count, like_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article['title'],
                article['content'],
                article['author'],
                article['category'],
                article['status'],
                datetime.now().isoformat(),
                0,  # view_count
                0   # like_count
            ))
        
        # 提交更改
        conn.commit()
        print(f"成功添加了 {len(test_articles)} 篇测试文章")
        
        # 查询并显示添加的文章
        cursor.execute("SELECT id, title, author, category FROM articles ORDER BY id DESC LIMIT 10")
        articles = cursor.fetchall()
        
        print("\n当前文章列表：")
        for article in articles:
            print(f"ID: {article[0]}, 标题: {article[1]}, 作者: {article[2]}, 分类: {article[3]}")
            
    except Exception as e:
        print(f"添加测试文章时出错: {e}")
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_test_articles()
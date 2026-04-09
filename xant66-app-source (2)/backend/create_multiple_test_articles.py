#!/usr/bin/env python3
"""
创建多篇测试文章用于测试审核功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db_articles import add_article

def create_test_articles():
    """创建多篇测试文章"""
    
    test_articles = [
        {
            "title": "测试文章1 - 科技新闻",
            "content": "这是第一篇测试文章，内容关于最新的科技发展趋势。人工智能技术正在快速发展，为各行各业带来了新的机遇和挑战。",
            "author": "admin",
            "category": "科技互助分享"
        },
        {
            "title": "测试文章2 - 学习心得",
            "content": "这是第二篇测试文章，分享一些学习编程的心得体会。学习编程需要持之以恒，多动手实践，不断总结经验。",
            "author": "admin", 
            "category": "内科互助分享"
        },
        {
            "title": "测试文章3 - 生活感悟",
            "content": "这是第三篇测试文章，记录一些生活中的感悟和思考。生活中的点点滴滴都值得我们去珍惜和感悟。",
            "author": "admin",
            "category": "皮肤科互助分享"
        },
        {
            "title": "测试文章4 - 技术分享",
            "content": "这是第四篇测试文章，分享一些实用的技术知识。掌握新技术需要理论与实践相结合，不断学习和探索。",
            "author": "admin",
            "category": "外科互助分享"
        },
        {
            "title": "测试文章5 - 经验总结",
            "content": "这是第五篇测试文章，总结一些工作和学习中的经验。经验的积累是一个循序渐进的过程，需要时间和耐心。",
            "author": "admin",
            "category": "儿科互助分享"
        }
    ]
    
    created_articles = []
    
    for i, article_data in enumerate(test_articles, 1):
        try:
            # 调用add_article函数创建文章
            article_id = add_article(
                title=article_data["title"],
                content=article_data["content"],
                author=article_data["author"],
                category=article_data["category"]
            )
            
            created_articles.append({
                "id": article_id,
                "title": article_data["title"]
            })
            
            print(f"✅ 成功创建测试文章 {i}: ID={article_id}, 标题='{article_data['title']}'")
            
        except Exception as e:
            print(f"❌ 创建测试文章 {i} 失败: {str(e)}")
    
    print(f"\n📊 总结: 成功创建了 {len(created_articles)} 篇测试文章")
    for article in created_articles:
        print(f"   - ID {article['id']}: {article['title']}")
    
    return created_articles

if __name__ == "__main__":
    print("🚀 开始创建多篇测试文章...")
    create_test_articles()
    print("✨ 测试文章创建完成！")
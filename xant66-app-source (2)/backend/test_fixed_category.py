#!/usr/bin/env python3
"""
测试修复后的分类功能
"""
import requests
import json

# 服务器地址
BASE_URL = "http://127.0.0.1:8001"

# 测试修复后的分类功能
def test_fixed_category():
    # 登录获取token
    login_data = {
        "username": "洪汉博",
        "password": "15157112180@Cuz"
    }
    
    print("1. 登录...")
    login_response = requests.post(f"{BASE_URL}/api/login", json=login_data)
    
    if login_response.status_code != 200:
        print("登录失败!")
        return
    
    token = login_response.json().get("access_token")
    print(f"获取到token: {token[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 创建一篇新文章，使用新的分类名称
    print(f"\n2. 创建测试文章（使用新分类名称）...")
    article_data = {
        "title": "测试修复后的分类功能",
        "content": "这是一篇测试文章，用于验证分类名称修复后，帖子能否正确显示在对应分类下。",
        "category": "内科"
    }
    
    response = requests.post(f"{BASE_URL}/api/articles/submit", json=article_data, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        article_id = data.get("article_id")
        print(f"✅ 文章创建成功! 文章ID: {article_id}")
        
        # 审核文章
        print(f"\n3. 审核文章...")
        audit_data = {
            "article_id": article_id,
            "audit_status": "approved"
        }
        
        audit_response = requests.post(f"{BASE_URL}/api/admin/article/audit", json=audit_data, headers=headers)
        
        if audit_response.status_code == 200:
            print(f"✅ 文章审核通过")
            
            # 测试获取分类文章
            print(f"\n4. 测试获取分类文章（内科）...")
            category_response = requests.get(f"{BASE_URL}/api/articles/categories/内科", headers=headers)
            
            if category_response.status_code == 200:
                category_data = category_response.json()
                articles = category_data.get('articles', [])
                print(f"✅ 成功获取 {len(articles)} 篇文章")
                
                # 检查新文章是否在列表中
                found = False
                for article in articles:
                    if article['id'] == article_id:
                        found = True
                        print(f"✅ 新文章成功显示在分类中!")
                        print(f"   标题: {article['title']}")
                        print(f"   分类: {article['category']}")
                        break
                
                if not found:
                    print(f"❌ 新文章未在分类中找到")
            else:
                print(f"❌ 获取分类文章失败: {category_response.text}")
        else:
            print(f"❌ 文章审核失败: {audit_response.text}")
    else:
        print(f"❌ 文章创建失败: {response.text}")

if __name__ == "__main__":
    print("=== 测试修复后的分类功能 ===")
    test_fixed_category()

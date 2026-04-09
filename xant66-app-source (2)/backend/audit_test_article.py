#!/usr/bin/env python3
"""
审核测试文章的脚本
"""
import requests
import json

# 服务器地址
BASE_URL = "http://127.0.0.1:8001"

# 审核文章
def audit_article(article_id):
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
    
    # 审核文章
    print(f"\n2. 审核文章 {article_id}...")
    audit_data = {
        "article_id": article_id,
        "audit_status": "approved"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(f"{BASE_URL}/api/admin/article/audit", json=audit_data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ 文章审核成功!")
        print(f"文章ID: {data.get('article_id')}")
        print(f"状态: {data.get('status')}")
        print(f"审核员: {data.get('audited_by')}")
        
        # 测试获取分类文章
        print(f"\n3. 测试获取分类文章...")
        test_category_articles(headers)
    else:
        print("❌ 文章审核失败")

# 测试获取分类文章
def test_category_articles(headers):
    response = requests.get(f"{BASE_URL}/api/articles/categories/测试分类", headers=headers)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 获取分类文章成功!")
        print(f"文章数量: {len(data.get('articles', []))}")
        if data.get('articles'):
            for article in data['articles']:
                print(f"  - {article['title']}")
    else:
        print(f"❌ 获取分类文章失败: {response.text}")

if __name__ == "__main__":
    print("=== 审核测试文章 ===")
    audit_article(1)  # 审核ID为1的文章

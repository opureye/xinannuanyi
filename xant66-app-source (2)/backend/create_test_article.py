#!/usr/bin/env python3
"""
创建测试文章的脚本
"""
import requests
import json

# 服务器地址
BASE_URL = "http://127.0.0.1:8001"

# 登录并创建测试文章
def create_test_article():
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
    
    # 创建测试文章
    print("\n2. 创建测试文章...")
    article_data = {
        "title": "测试文章标题 - 用于审核功能测试",
        "content": "这是一篇测试文章的内容，用于验证文章审核页面的功能是否正常。文章应该能够正确加载并显示在审核页面中。这个测试将帮助我们确认数据库字段修复是否成功。",
        "category": "测试分类"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(f"{BASE_URL}/api/articles/submit", json=article_data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        article_id = data.get("article_id")
        print(f"\n✅ 测试文章创建成功! 文章ID: {article_id}")
        
        # 测试获取文章详情
        print(f"\n3. 测试获取文章详情 (ID: {article_id})...")
        detail_response = requests.get(f"{BASE_URL}/api/articles/{article_id}", headers=headers)
        print(f"状态码: {detail_response.status_code}")
        
        if detail_response.status_code == 200:
            detail_data = detail_response.json()
            print(f"✅ 文章详情获取成功!")
            print(f"标题: {detail_data['article']['title']}")
            print(f"内容: {detail_data['article']['content'][:50]}...")
        else:
            print(f"❌ 文章详情获取失败: {detail_response.text}")
    else:
        print("❌ 文章创建失败")

if __name__ == "__main__":
    print("=== 创建测试文章 ===")
    create_test_article()

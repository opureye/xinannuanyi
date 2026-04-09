#!/usr/bin/env python3
"""
测试分类API的脚本
"""
import requests
import json

# 服务器地址
BASE_URL = "http://127.0.0.1:8001"

# 测试分类API
def test_category_apis():
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
    
    # 测试各个分类
    categories = ["内科", "外科", "心理科", "皮肤科", "妇产科", "儿科", "神经科", "中医科", "肿瘤科"]
    
    print(f"\n2. 测试各分类文章API...")
    for category in categories:
        print(f"\n--- 测试分类: {category} ---")
        response = requests.get(f"{BASE_URL}/api/articles/categories/{category}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            print(f"✅ 成功获取 {len(articles)} 篇文章")
            for article in articles:
                print(f"   - {article['title']}")
        else:
            print(f"❌ 获取失败: {response.text}")
    
    # 测试获取所有文章
    print(f"\n3. 测试获取所有已审核文章...")
    response = requests.get(f"{BASE_URL}/api/articles", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        articles = data.get('articles', [])
        print(f"✅ 成功获取 {len(articles)} 篇文章")
    else:
        print(f"❌ 获取失败: {response.text}")
    
    # 测试搜索功能
    print(f"\n4. 测试搜索功能...")
    search_data = {
        "keyword": "预防"
    }
    response = requests.post(f"{BASE_URL}/api/articles/search", json=search_data, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        print(f"✅ 搜索成功，找到 {len(results)} 篇文章")
        for article in results:
            print(f"   - {article['title']}")
    else:
        print(f"❌ 搜索失败: {response.text}")

if __name__ == "__main__":
    print("=== 测试分类API ===")
    test_category_apis()

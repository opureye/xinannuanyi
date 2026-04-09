#!/usr/bin/env python3
"""
测试API的脚本 - 修复版
"""
import requests
import json

# 服务器地址
BASE_URL = "http://127.0.0.1:8001"

# 测试待审核文章API
def test_pending_articles_api():
    # 首先登录获取token
    login_data = {
        "username": "洪汉博",
        "password": "15157112180@Cuz"
    }
    
    print("1. 登录管理员账户...")
    login_response = requests.post(f"{BASE_URL}/api/login", json=login_data)
    print(f"登录状态码: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print("登录失败!")
        print(f"响应内容: {login_response.text}")
        return
    
    login_result = login_response.json()
    token = login_result.get("access_token")
    print(f"获取到token: {token[:20]}...")
    
    # 设置认证头
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试待审核文章API
    print("\n2. 测试待审核文章API...")
    url = f"{BASE_URL}/api/admin/articles/pending"
    print(f"请求URL: {url}")
    
    response = requests.get(url, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"解析后的数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # 如果有待审核文章，测试第一个文章的详情API
        if data.get('articles') and len(data['articles']) > 0:
            article_id = data['articles'][0]['id']
            print(f"\n3. 测试文章详情API (ID: {article_id})...")
            test_article_detail_api(article_id, headers)
        else:
            print("\n没有待审核文章")
    else:
        print("API请求失败")

# 测试文章详情API
def test_article_detail_api(article_id, headers):
    url = f"{BASE_URL}/api/articles/{article_id}"
    print(f"请求URL: {url}")
    
    response = requests.get(url, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"解析后的数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    else:
        print("API请求失败")

if __name__ == "__main__":
    print("=== 测试API ===")
    test_pending_articles_api()

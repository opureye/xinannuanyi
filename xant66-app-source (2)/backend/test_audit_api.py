#!/usr/bin/env python3
"""
测试审核API的脚本
"""
import requests
import json

# 服务器地址
BASE_URL = "http://127.0.0.1:8001"

def test_audit_api():
    """测试审核API"""
    
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
        return
    
    login_result = login_response.json()
    token = login_result.get("access_token")
    print(f"获取到token: {token[:20]}...")
    
    # 设置认证头
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 获取待审核文章
    print("\n2. 获取待审核文章...")
    pending_response = requests.get(f"{BASE_URL}/admin/articles/pending", headers=headers)
    print(f"获取待审核文章状态码: {pending_response.status_code}")
    
    if pending_response.status_code == 200:
        pending_articles = pending_response.json()
        print(f"待审核文章数量: {len(pending_articles.get('articles', []))}")
        
        if pending_articles.get('articles'):
            article = pending_articles['articles'][0]
            article_id = article['id']
            print(f"测试文章ID: {article_id}, 标题: {article['title']}")
            
            # 测试审核API
            print(f"\n3. 测试审核文章 {article_id}...")
            audit_data = {
                "article_id": article_id,
                "audit_status": "approved"
            }
            
            audit_response = requests.post(f"{BASE_URL}/admin/article/audit", 
                                         headers=headers, 
                                         json=audit_data)
            print(f"审核API状态码: {audit_response.status_code}")
            print(f"审核API响应: {audit_response.text}")
            
            if audit_response.status_code == 200:
                audit_result = audit_response.json()
                print("✅ 审核API测试成功!")
                print(f"审核结果: {audit_result}")
            else:
                print("❌ 审核API测试失败!")
        else:
            print("没有待审核文章")
    else:
        print(f"获取待审核文章失败: {pending_response.text}")

if __name__ == "__main__":
    test_audit_api()

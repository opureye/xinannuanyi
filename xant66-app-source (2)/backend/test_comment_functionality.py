#!/usr/bin/env python3
"""
测试评论功能的脚本
"""
import requests
import json

# 服务器地址
BASE_URL = "http://127.0.0.1:8001"

# 测试评论功能
def test_comment_functionality():
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
    
    # 获取一篇文章ID
    print(f"\n2. 获取文章列表...")
    articles_response = requests.get(f"{BASE_URL}/api/articles", headers=headers)
    
    if articles_response.status_code != 200:
        print("获取文章列表失败!")
        return
    
    articles_data = articles_response.json()
    articles = articles_data.get('articles', [])
    
    if not articles:
        print("没有可用的文章")
        return
    
    article_id = articles[0]['id']
    print(f"使用文章ID: {article_id}, 标题: {articles[0]['title']}")
    
    # 测试添加评论
    print(f"\n3. 测试添加评论...")
    comment_data = {
        "content": "这是一条测试评论，用于验证评论功能是否正常工作。"
    }
    
    comment_response = requests.post(
        f"{BASE_URL}/api/articles/{article_id}/comments",
        json=comment_data,
        headers=headers
    )
    
    print(f"状态码: {comment_response.status_code}")
    print(f"响应内容: {comment_response.text}")
    
    if comment_response.status_code == 200:
        comment_result = comment_response.json()
        comment_id = comment_result.get('comment_id')
        print(f"✅ 评论添加成功! 评论ID: {comment_id}")
        
        # 测试获取待审核评论
        print(f"\n4. 测试获取待审核评论...")
        pending_response = requests.get(f"{BASE_URL}/api/comments/pending", headers=headers)
        
        if pending_response.status_code == 200:
            pending_data = pending_response.json()
            comments = pending_data.get('comments', [])
            print(f"✅ 获取到 {len(comments)} 条待审核评论")
            
            if comments:
                print(f"最新评论: {comments[0]['content'][:50]}...")
                
                # 测试审核评论
                print(f"\n5. 测试审核评论...")
                audit_data = {
                    "action": "approve"
                }
                
                audit_response = requests.post(
                    f"{BASE_URL}/api/comments/{comment_id}/audit",
                    json=audit_data,
                    headers=headers
                )
                
                print(f"状态码: {audit_response.status_code}")
                print(f"响应内容: {audit_response.text}")
                
                if audit_response.status_code == 200:
                    print(f"✅ 评论审核成功!")
                else:
                    print(f"❌ 评论审核失败")
        else:
            print(f"❌ 获取待审核评论失败: {pending_response.text}")
    else:
        print(f"❌ 评论添加失败")

if __name__ == "__main__":
    print("=== 测试评论功能 ===")
    test_comment_functionality()

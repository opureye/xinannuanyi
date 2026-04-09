import requests
import json

# 测试待审核文章API
def test_pending_articles_api():
    url = "http://localhost:8001/admin/articles/pending"
    headers = {
        "Authorization": "Bearer admin_token_123"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"解析后的数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"请求失败: {e}")

# 测试具体文章API
def test_article_api(article_id):
    url = f"http://localhost:8001/api/articles/{article_id}"
    headers = {
        "Authorization": "Bearer admin_token_123"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\n=== 文章 {article_id} API 测试 ===")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"解析后的数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    print("=== 测试待审核文章API ===")
    test_pending_articles_api()
    
    print("\n=== 测试具体文章API ===")
    test_article_api(8)  # 测试ID为8的文章
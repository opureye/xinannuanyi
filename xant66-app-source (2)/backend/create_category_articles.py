#!/usr/bin/env python3
"""
创建多个不同分类的测试文章
"""
import requests
import json

# 服务器地址
BASE_URL = "http://127.0.0.1:8001"

# 登录并创建测试文章
def create_test_articles():
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
    
    # 创建多个不同分类的测试文章
    articles = [
        {
            "title": "内科常见疾病预防与护理",
            "content": "内科是医学的一个分支，主要研究内脏器官的疾病。常见的内科疾病包括高血压、糖尿病、心脏病等。预防内科疾病需要注意饮食健康、适量运动、定期体检等。",
            "category": "内科"
        },
        {
            "title": "外科手术前后注意事项",
            "content": "外科手术是治疗疾病的重要手段。手术前需要做好充分准备，包括心理准备、身体检查等。手术后需要注意伤口护理、饮食调整、适当休息等。",
            "category": "外科"
        },
        {
            "title": "心理压力缓解技巧",
            "content": "现代生活中，心理压力是常见问题。可以通过运动、冥想、听音乐、与朋友交流等方式缓解压力。如果压力过大，建议寻求专业心理咨询师的帮助。",
            "category": "心理科"
        },
        {
            "title": "皮肤科过敏反应的应对方法",
            "content": "皮肤过敏是常见的皮肤科问题。常见的过敏原包括花粉、食物、药物等。出现过敏反应时，应立即停止接触过敏原，并寻求医生帮助。",
            "category": "皮肤科"
        },
        {
            "title": "妇产科孕期保健指南",
            "content": "孕期保健对母婴健康至关重要。孕妇需要定期产检、合理饮食、适当运动、保持良好心态。同时要避免接触有害物质，保证充足睡眠。",
            "category": "妇产科"
        },
        {
            "title": "儿科常见病防治",
            "content": "儿童免疫系统尚未发育完全，容易患各种疾病。家长要注意儿童的个人卫生、营养均衡、按时接种疫苗。发现异常及时就医。",
            "category": "儿科"
        },
        {
            "title": "神经科疾病早期症状识别",
            "content": "神经科疾病包括中风、帕金森病、阿尔茨海默病等。早期识别症状对治疗非常重要。常见的早期症状包括头痛、记忆力下降、运动障碍等。",
            "category": "神经科"
        },
        {
            "title": "中医调理身体的方法",
            "content": "中医是中国传统医学的重要组成部分。中医调理身体的方法包括中药、针灸、推拿、食疗等。中医强调阴阳平衡、气血调和。",
            "category": "中医科"
        },
        {
            "title": "肿瘤科患者心理疏导",
            "content": "肿瘤患者常面临巨大的心理压力。心理疏导可以帮助患者建立积极的心态，提高生活质量。家属的支持和理解也非常重要。",
            "category": "肿瘤科"
        }
    ]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    created_articles = []
    
    for i, article_data in enumerate(articles, 1):
        print(f"\n{i}. 创建文章: {article_data['title']}")
        
        response = requests.post(f"{BASE_URL}/api/articles/submit", json=article_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            article_id = data.get("article_id")
            print(f"   ✅ 创建成功! 文章ID: {article_id}")
            created_articles.append({
                "id": article_id,
                "title": article_data['title'],
                "category": article_data['category']
            })
        else:
            print(f"   ❌ 创建失败: {response.text}")
    
    print(f"\n✅ 共创建 {len(created_articles)} 篇文章")
    
    # 审核所有文章
    print(f"\n开始审核文章...")
    for article in created_articles:
        audit_data = {
            "article_id": article['id'],
            "audit_status": "approved"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/article/audit", json=audit_data, headers=headers)
        
        if response.status_code == 200:
            print(f"   ✅ 文章 {article['title']} 审核通过")
        else:
            print(f"   ❌ 文章 {article['title']} 审核失败: {response.text}")
    
    print(f"\n✅ 所有文章已审核通过！")
    print(f"\n现在可以在分类页面查看不同分类的帖子了")
    print(f"访问地址: http://localhost:8001/16 post_category.html")

if __name__ == "__main__":
    print("=== 创建多个分类的测试文章 ===")
    create_test_articles()

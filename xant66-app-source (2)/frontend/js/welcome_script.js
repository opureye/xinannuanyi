// 搜索功能
async function handleSearch(event) {
    if (event.key === 'Enter') {
        const searchTerm = event.target.value.toLowerCase().trim();
        if (searchTerm) {
            try {
                // 显示加载状态
                const articleList = document.querySelector('.article-list');
                const originalContent = articleList.innerHTML;
                articleList.innerHTML = '<div class="loading">正在搜索中...</div>';
                
                // 调用API进行搜索
                const response = await fetch(`${window.location.origin}/api/articles/search`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${sessionStorage.getItem('auth_token')}`
                    },
                    body: JSON.stringify({ keyword: searchTerm })
                });
                
                const data = await response.json();
                
                if (response.ok && data.status === "success") {
                    // 清空列表
                    articleList.innerHTML = '';
                    
                    if (data.results && data.results.length > 0) {
                        // 添加搜索结果
                        data.results.forEach(article => {
                            const articleItem = document.createElement('div');
                            articleItem.className = 'article-item';
                            articleItem.innerHTML = `<a href="6 article.html?id=${article.id}">${article.title}</a>`;
                            articleList.appendChild(articleItem);
                        });
                    } else {
                        // 显示无结果提示
                        articleList.innerHTML = '<div class="no-results">未找到匹配的文章</div>';
                    }
                } else {
                    // 恢复原始内容
                    articleList.innerHTML = originalContent;
                    alert(data.message || '搜索失败，请稍后重试');
                }
            } catch (error) {
                console.error('搜索失败:', error);
                // 恢复原始内容
                const articleList = document.querySelector('.article-list');
                if (articleList) {
                    articleList.innerHTML = '搜索过程中发生错误，请检查您的网络连接';
                }
            }
        }
    }
}

// 加载文章列表
async function loadArticleList() {
    try {
        console.log('开始加载文章列表...');
        const articleList = document.querySelector('.article-list');
        
        if (!articleList) {
            console.error('未找到 .article-list 元素');
            return;
        }
        
        // 显示加载状态
        articleList.innerHTML = '<div class="loading">正在加载文章列表...</div>';
        
        // 调用API获取文章列表 - 只获取已审核通过的文章
        console.log('发送API请求到: /api/articles');
        const response = await fetch(`${window.location.origin}/api/articles`);
        
        console.log('API响应状态:', response.status, response.statusText);
        
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('API响应数据:', data);
        
        if (data.status === "success") {
            // 清空列表
            articleList.innerHTML = '';
            
            if (data.articles && data.articles.length > 0) {
                console.log(`找到 ${data.articles.length} 篇文章`);
                // 添加文章列表
                data.articles.forEach(article => {
                    const articleItem = document.createElement('div');
                    articleItem.className = 'article-item';
                    articleItem.innerHTML = `<a href="6 article.html?id=${article.id}">${article.title}</a>`;
                    articleList.appendChild(articleItem);
                });
                console.log('文章列表加载完成');
            } else {
                console.log('没有找到文章');
                // 显示无文章提示
                articleList.innerHTML = '<div class="no-results">暂无文章</div>';
            }
        } else {
            console.error('API返回错误状态:', data.status);
            articleList.innerHTML = '加载文章列表失败';
        }
    } catch (error) {
        console.error('加载文章列表失败:', error);
        const articleList = document.querySelector('.article-list');
        if (articleList) {
            articleList.innerHTML = `加载过程中发生错误: ${error.message}`;
        }
    }
}

// 页面加载完成后执行
// 导入退出登录功能
import { initReloginButtons } from './auth.js';

window.addEventListener('DOMContentLoaded', function() {
    // 初始化重新登录按钮的事件处理
    initReloginButtons();
    
    // 获取搜索框
    const searchInput = document.getElementById('searchInput');
    
    if (searchInput) {
        // 添加搜索事件监听
        searchInput.addEventListener('keypress', handleSearch);
    }
    
    // 加载文章列表
    loadArticleList();
});

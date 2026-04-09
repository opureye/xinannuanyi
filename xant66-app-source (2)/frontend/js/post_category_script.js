/**
 * 显示通知消息
 * @param {string} message - 通知消息内容
 * @param {string} type - 通知类型：'info', 'success', 'error', 'warning'
 */
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `fixed bottom-4 right-4 p-4 rounded-lg shadow-lg z-50 max-w-xs transition-all duration-300 ease-in-out transform translate-y-4 opacity-0`;
    
    // 根据类型设置样式
    switch(type) {
        case 'success':
            notification.classList.add('bg-green-500', 'text-white');
            notification.innerHTML = `<i class="fas fa-check-circle mr-2"></i>${message}`;
            break;
        case 'error':
            notification.classList.add('bg-red-500', 'text-white');
            notification.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i>${message}`;
            break;
        case 'warning':
            notification.classList.add('bg-yellow-500', 'text-white');
            notification.innerHTML = `<i class="fas fa-exclamation-triangle mr-2"></i>${message}`;
            break;
        default:
            notification.classList.add('bg-blue-500', 'text-white');
            notification.innerHTML = `<i class="fas fa-info-circle mr-2"></i>${message}`;
    }
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 入场动画
    setTimeout(() => {
        notification.style.transform = 'translateY(0)';
        notification.style.opacity = '1';
    }, 10);
    
    // 自动消失
    setTimeout(() => {
        notification.style.transform = 'translateY(20px)';
        notification.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
}

/**
 * 初始化分类页面交互
 */
function initCategoryPage() {
    // 为分类列表项添加点击事件
    const categoryLinks = document.querySelectorAll('.category-list a');
    categoryLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const categoryName = this.getAttribute('data-category') || this.textContent.trim();
            showNotification(`正在加载 ${categoryName} 分类的帖子...`, 'info');
            
            // 加载分类内容
            loadCategoryContent(categoryName);
        });
    });
    
    // 为搜索按钮添加点击事件
    const searchButton = document.getElementById('search-button');
    const searchInput = document.getElementById('category-search-input');
    
    if (searchButton && searchInput) {
        searchButton.addEventListener('click', function() {
            performSearch();
        });
        
        // 添加回车搜索功能
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
    
    // 添加页面加载完成的通知
    showNotification('帖子分类页面加载完成', 'success');
}

/**
 * 执行搜索操作
 */
function performSearch() {
    const searchInput = document.getElementById('category-search-input');
    const categoryNameElement = document.getElementById('category-name');
    
    if (searchInput && categoryNameElement) {
        const keyword = searchInput.value.trim();
        const currentCategory = categoryNameElement.textContent || '全部';
        
        if (!keyword) {
            showNotification('请输入搜索关键词', 'warning');
            return;
        }
        
        showNotification(`正在搜索 ${currentCategory} 分类中包含 "${keyword}" 的帖子...`, 'info');
        loadCategoryContent(currentCategory, keyword);
    }
}

/**
 * 加载分类内容
 * @param {string} category - 分类名称
 * @param {string} [keyword=''] - 搜索关键词
 */
async function loadCategoryContent(category, keyword = '') {
    try {
        // 显示加载状态
        const resultsList = document.getElementById('results-list');
        const currentCategoryElement = document.getElementById('current-category');
        const categoryNameElement = document.getElementById('category-name');
        
        if (resultsList && currentCategoryElement && categoryNameElement) {
            resultsList.innerHTML = '<p class="text-gray-500">正在加载...</p>';
            
            // 更新当前分类显示
            currentCategoryElement.classList.remove('hidden');
            categoryNameElement.textContent = category;
            
            // 调用真实API获取分类帖子
            let posts = [];
            try {
                if (keyword) {
                    // 搜索模式
                    posts = await searchPostsByKeyword(keyword, category);
                } else if (category === '全部') {
                    // 获取所有已审核的帖子
                    posts = await fetchAllApprovedArticles();
                } else {
                    // 获取指定分类的帖子
                    posts = await fetchArticlesByCategory(category);
                }
            } catch (apiError) {
                console.warn('API调用失败，使用空结果:', apiError);
                posts = [];
            }
            
            // 显示搜索结果
            if (posts.length > 0) {
                renderSearchResults(posts);
                showNotification(`${category} 分类的帖子加载完成，共找到 ${posts.length} 条结果`, 'success');
            } else {
                resultsList.innerHTML = '<p class="text-gray-500">未找到相关帖子</p>';
                showNotification(`未找到 ${category} 分类中相关的帖子`, 'info');
            }
        }
    } catch (error) {
        console.error('加载分类内容失败:', error);
        showNotification('加载分类内容失败，请稍后再试', 'error');
    }
}

/**
 * 从API获取指定分类的文章
 * @param {string} category - 分类名称
 * @returns {Promise<Array>} - 文章列表
 */
async function fetchArticlesByCategory(category) {
    const token = sessionStorage.getItem('auth_token');
    const response = await fetch(`${window.location.origin}/api/articles/categories/${encodeURIComponent(category)}`, {
        method: 'GET',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    
    if (!response.ok) {
        throw new Error(`API请求失败: ${response.status}`);
    }
    
    const data = await response.json();
    return data.articles || data || [];
}

/**
 * 获取所有已审核通过的文章
 * @returns {Promise<Array>} - 文章列表
 */
async function fetchAllApprovedArticles() {
    const token = sessionStorage.getItem('auth_token');
    const response = await fetch(`${window.location.origin}/api/articles`, {
        method: 'GET',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    
    if (!response.ok) {
        throw new Error(`API请求失败: ${response.status}`);
    }
    
    const data = await response.json();
    return data.articles || data || [];
}

/**
 * 搜索文章
 * @param {string} keyword - 搜索关键词
 * @param {string} category - 分类名称（可选）
 * @returns {Promise<Array>} - 文章列表
 */
async function searchPostsByKeyword(keyword, category = '') {
    const token = sessionStorage.getItem('auth_token');
    
    const response = await fetch(`${window.location.origin}/api/articles/search`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ keyword: keyword, category: category })
    });
    
    if (!response.ok) {
        throw new Error(`API请求失败: ${response.status}`);
    }
    
    const data = await response.json();
    return data.results || data.articles || data || [];
}

/**
 * 模拟搜索帖子（用于演示）
 * @param {string} category - 分类名称
 * @param {string} [keyword=''] - 搜索关键词
 * @returns {Promise<Array>} - 模拟的帖子列表
 */
async function simulateSearchPosts(category, keyword = '') {
    // 为了演示效果，创建一些模拟帖子数据
    const mockPosts = [
        { id: 1, title: '内科常见疾病预防与护理', category: '内科', author: '张医生', createdAt: '2023-10-15' },
        { id: 2, title: '外科手术前后注意事项', category: '外科', author: '李医生', createdAt: '2023-10-10' },
        { id: 3, title: '皮肤科过敏反应的应对方法', category: '皮肤科', author: '王医生', createdAt: '2023-10-05' },
        { id: 4, title: '妇产科孕期保健指南', category: '妇产科', author: '赵医生', createdAt: '2023-09-28' },
        { id: 5, title: '儿科常见病防治', category: '儿科', author: '孙医生', createdAt: '2023-09-20' },
        { id: 6, title: '神经科疾病早期症状识别', category: '神经科', author: '周医生', createdAt: '2023-09-15' },
        { id: 7, title: '中医调理身体的方法', category: '中医科', author: '吴医生', createdAt: '2023-09-10' },
        { id: 8, title: '肿瘤科患者心理疏导', category: '肿瘤科', author: '郑医生', createdAt: '2023-09-05' },
        { id: 9, title: '心理压力缓解技巧', category: '心理科', author: '冯医生', createdAt: '2023-08-30' },
    ];
    
    // 模拟网络延迟
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // 根据分类和关键词过滤帖子
    return mockPosts.filter(post => {
        const categoryMatch = category === '全部' || post.category === category;
        const keywordMatch = !keyword || 
            post.title.includes(keyword) || 
            post.content?.includes(keyword) ||
            post.category.includes(keyword);
        return categoryMatch && keywordMatch;
    });
}

/**
 * 渲染搜索结果
 * @param {Array} posts - 帖子列表
 */
function renderSearchResults(posts) {
    const resultsList = document.getElementById('results-list');
    
    if (resultsList) {
        if (posts.length === 0) {
            resultsList.innerHTML = '<p class="text-gray-500">未找到相关帖子</p>';
            return;
        }
        
        let html = '';
        posts.forEach(post => {
            html += `
                <div class="post-item bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
                    <h3 class="text-lg font-semibold text-gray-800 mb-2">
                        <a href="6 article.html?id=${post.id}" class="hover:text-green-600 transition-colors">${post.title}</a>
                    </h3>
                    <div class="text-sm text-gray-500">
                        <span>${post.category}</span>
                        <span class="mx-2">•</span>
                        <span>${post.author}</span>
                        <span class="mx-2">•</span>
                        <span>${post.createdAt}</span>
                    </div>
                </div>
            `;
        });
        
        resultsList.innerHTML = html;
    }
}

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    // 初始化分类页面交互
    initCategoryPage();
    
    // 添加平滑滚动效果
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            if (this.getAttribute('href') === '#') {
                e.preventDefault();
            } else {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});

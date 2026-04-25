import { showNotification } from './utils.js';

// 等待DOM内容加载完成
window.addEventListener('DOMContentLoaded', function() {
    // 检查认证状态
    const token = sessionStorage.getItem('auth_token');
    if (!token) {
        showNotification('请先登录管理员账户', 'error');
        window.location.href = '4 login.html';
        return;
    }
    
    // 更新文章计数器显示
    function updateArticleCounter() {
        const counterElement = document.getElementById('article-counter');
        if (counterElement && pendingArticles.length > 0) {
            counterElement.textContent = `第 ${currentArticleIndex + 1} 篇，共 ${pendingArticles.length} 篇`;
        }
        
        // 更新导航按钮状态
        const prevBtn = document.getElementById('prev-article');
        const nextBtn = document.getElementById('next-article');
        
        if (prevBtn) {
            prevBtn.disabled = currentArticleIndex <= 0;
        }
        
        if (nextBtn) {
            nextBtn.disabled = currentArticleIndex >= pendingArticles.length - 1;
        }
    }
    
    // 导航到上一篇文章
    function navigateToPrevious() {
        if (currentArticleIndex > 0) {
            currentArticleIndex--;
            const article = pendingArticles[currentArticleIndex];
            currentArticleId = article.id;
            loadArticle(currentArticleId);
            updateArticleCounter();
        }
    }
    
    // 导航到下一篇文章
    function navigateToNext() {
        if (currentArticleIndex < pendingArticles.length - 1) {
            currentArticleIndex++;
            const article = pendingArticles[currentArticleIndex];
            currentArticleId = article.id;
            loadArticle(currentArticleId);
            updateArticleCounter();
        }
    }
    
    // 添加导航按钮事件监听器
    const prevBtn = document.getElementById('prev-article');
    const nextBtn = document.getElementById('next-article');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', navigateToPrevious);
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', navigateToNext);
    }
    
    // 修改审核成功后的处理逻辑
    function handleAuditSuccess() {
        // 从待审核列表中移除当前文章
        if (pendingArticles.length > 0) {
            pendingArticles.splice(currentArticleIndex, 1);
            
            // 如果还有文章，加载下一篇
            if (pendingArticles.length > 0) {
                // 如果当前索引超出范围，调整到最后一篇
                if (currentArticleIndex >= pendingArticles.length) {
                    currentArticleIndex = pendingArticles.length - 1;
                }
                
                const nextArticle = pendingArticles[currentArticleIndex];
                currentArticleId = nextArticle.id;
                loadArticle(currentArticleId);
                updateArticleCounter();
            } else {
                // 没有更多文章了
                showStatus('所有文章已审核完成！', 'info');
                document.querySelector('h1').textContent = '审核完成';
                document.querySelector('.article-meta').innerHTML = '所有待审核文章已处理完毕';
                document.querySelector('.article-content p').textContent = '当前没有需要审核的文章。';
                
                // 禁用审核按钮
                if (approveBtn) approveBtn.disabled = true;
                if (rejectBtn) rejectBtn.disabled = true;
                
                // 更新计数器
                const counterElement = document.getElementById('article-counter');
                if (counterElement) {
                    counterElement.textContent = '已完成所有审核';
                }
            }
        }
    }
    
    // 获取页面元素
    const approveBtn = document.querySelector('.audit-btn.approve');
    const rejectBtn = document.querySelector('.audit-btn.reject');
    const statusDiv = document.getElementById('audit-status');
    
    // 从URL获取文章ID
    const urlParams = new URLSearchParams(window.location.search);
    const articleId = urlParams.get('id');
    
    // 声明全局变量以便在函数间共享
    let currentArticleId = articleId;
    let pendingArticles = []; // 存储所有待审核文章
    let currentArticleIndex = 0; // 当前文章在列表中的索引
    
    if (!currentArticleId) {
        currentArticleId = localStorage.getItem('currentAuditArticleId');
    }
    
    // 初始化页面时加载文章
    // 总是先加载所有待审核文章列表，然后根据currentArticleId决定显示哪一篇
    loadNextPendingArticle();
    
    // 加载文章内容
    async function loadArticle(id) {
        try {
            console.log('正在加载文章ID:', id);
            const response = await fetch(`${window.location.origin}/api/articles/${id}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${sessionStorage.getItem('auth_token')}`
                }
            });
            
            console.log('文章API响应状态:', response.status);
            const data = await response.json();
            console.log('文章API响应数据:', data);
            
            if (response.ok && data.status === 'success' && data.article) {
                const article = data.article;
                
                // 更新页面内容
                document.querySelector('h1').textContent = article.title;
                document.querySelector('.article-meta').innerHTML = `发布于 ${new Date(article.created_at).toLocaleDateString()} | 作者：${article.author}`;
                document.querySelector('.article-content p').textContent = article.content;
                
                // 如果有分类信息，显示分类
                if (article.category) {
                    const categoryElement = document.createElement('div');
                    categoryElement.className = 'article-category';
                    categoryElement.textContent = `分类：${article.category}`;
                    document.querySelector('.article-meta').appendChild(categoryElement);
                }
                
                // 保存当前审核的文章ID
                localStorage.setItem('currentAuditArticleId', id);
                
                // 启用审核按钮
                if (approveBtn) approveBtn.disabled = false;
                if (rejectBtn) rejectBtn.disabled = false;
                
                console.log('文章加载成功:', article.title);
            } else {
                showStatus('加载文章失败: ' + (data.message || '未知错误'), 'error');
            }
        } catch (error) {
            console.error('加载文章失败:', error);
            showStatus('网络错误，请检查您的连接', 'error');
        }
    }
    
    // 加载下一篇待审核文章
    // 加载下一个待审核文章
    async function loadNextPendingArticle() {
        try {
            console.log('正在加载待审核文章...');
            const token = sessionStorage.getItem('auth_token');
            console.log('使用的token:', token ? '存在' : '不存在');
            
            const response = await fetch(`${window.location.origin}/api/admin/articles/pending`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            console.log('API响应状态:', response.status);
            const data = await response.json();
            console.log('API响应数据:', data);
            
            if (response.ok && data.success && data.articles && data.articles.length > 0) {
                pendingArticles = data.articles;
                console.log(`找到 ${pendingArticles.length} 篇待审核文章`);
                
                // 如果有指定的currentArticleId，找到它在列表中的索引
                if (currentArticleId) {
                    const articleIndex = pendingArticles.findIndex(article => article.id == currentArticleId);
                    if (articleIndex !== -1) {
                        currentArticleIndex = articleIndex;
                    } else {
                        currentArticleIndex = 0; // 如果找不到指定文章，默认显示第一篇
                    }
                } else {
                    // 如果当前索引超出范围，重置为0
                    if (currentArticleIndex >= pendingArticles.length) {
                        currentArticleIndex = 0;
                    }
                }
                
                // 加载当前索引的文章
                const currentArticle = pendingArticles[currentArticleIndex];
                currentArticleId = currentArticle.id;
                loadArticle(currentArticleId);
                
                // 更新页面标题显示当前文章位置
                updateArticleCounter();
                
            } else if (response.status === 401) {
                showStatus('认证失败，请重新登录管理员账户', 'error');
                setTimeout(() => {
                    window.location.href = '4 login.html';
                }, 2000);
            } else {
                showStatus('当前没有待审核的文章', 'info');
                // 禁用审核按钮
                if (approveBtn) approveBtn.disabled = true;
                if (rejectBtn) rejectBtn.disabled = true;
                pendingArticles = [];
            }
        } catch (error) {
            console.error('加载待审核文章失败:', error);
            showStatus('网络错误，请检查您的连接', 'error');
        }
    }
    
    // 处理审核操作的函数
    async function handleAudit(decision) {
        if (!currentArticleId) {
            showStatus('没有找到需要审核的文章', 'error');
            return;
        }
        
        try {
            // 调用管理员审核API
            const response = await fetch(`${window.location.origin}/api/admin/article/audit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionStorage.getItem('auth_token')}`
                },
                body: JSON.stringify({
                    article_id: parseInt(currentArticleId),
                    audit_status: decision === 'approve' ? 'approved' : 'rejected'
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                if (decision === 'approve') {
                    showStatus('✅ 帖子已通过审核，将发布到论坛', 'approved');
                } else {
                    showStatus('❌ 帖子未通过审核，已被拒绝', 'rejected');
                }
                
                // 清除当前审核文章ID
                localStorage.removeItem('currentAuditArticleId');
                
                // 2秒后处理审核成功逻辑
                setTimeout(() => {
                    handleAuditSuccess();
                }, 2000);
            } else {
                showStatus(data.message || '审核操作失败，请稍后重试', 'error');
            }
        } catch (error) {
            console.error('提交审核结果失败:', error);
            showStatus('网络错误，请检查您的连接', 'error');
        }
    }
    
    // 显示审核状态的函数
    function showStatus(text, type = 'info') {
        if (!statusDiv) return;
        
        statusDiv.innerHTML = text;
        
        // 移除所有状态类
        statusDiv.className = 'audit-status';
        
        // 添加对应的状态类
        if (type === 'approved') {
            statusDiv.className = 'audit-status status-approved';
        } else if (type === 'rejected') {
            statusDiv.className = 'audit-status status-rejected';
        } else if (type === 'error') {
            statusDiv.className = 'audit-status status-error';
        }
        
        statusDiv.style.display = 'flex';
        
        // 只有错误和信息类型的状态需要自动隐藏
        if (type === 'error' || type === 'info') {
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 3000);
        }
    }
    
    // 添加审核按钮点击事件
    if (approveBtn) {
        approveBtn.addEventListener('click', () => handleAudit('approve'));
    }
    
    if (rejectBtn) {
        rejectBtn.addEventListener('click', () => handleAudit('reject'));
    }
    
    // 加载举报信息
    if (currentArticleId) {
        loadComplaints(currentArticleId);
    }
    
    // 加载举报信息的函数
    async function loadComplaints(articleId) {
        try {
            const response = await fetch(`${window.location.origin}/api/articles/${articleId}/complaints`, {
                headers: {
                    'Authorization': `Bearer ${sessionStorage.getItem('auth_token')}`
                }
            });
            
            const data = await response.json();
            const complaintsContainer = document.getElementById('complaints-container');
            
            if (response.ok && data.success && complaintsContainer) {
                if (data.complaints && data.complaints.length > 0) {
                    complaintsContainer.innerHTML = '<h4>举报信息:</h4>';
                    data.complaints.forEach(complaint => {
                        const complaintElement = document.createElement('div');
                        complaintElement.className = 'complaint-item';
                        complaintElement.innerHTML = `<p><strong>举报人:</strong> ${complaint.reporter}</p><p><strong>理由:</strong> ${complaint.reason}</p>`;
                        complaintsContainer.appendChild(complaintElement);
                    });
                } else {
                    complaintsContainer.innerHTML = '<p class="no-complaints">暂无举报信息</p>';
                }
            }
        } catch (error) {
            console.error('加载举报信息失败:', error);
        }
    }
});

// 导入认证相关功能
import { logout, initReloginButtons } from './auth.js';

// 等待DOM加载完成
window.addEventListener('DOMContentLoaded', async function() {
    try {
        console.log('审计页面初始化开始');
        
        // 检查用户权限
        const token = sessionStorage.getItem('auth_token');
        if (!token) {
            alert('请先登录');
            window.location.href = '4 login.html';
            return;
        }
        
        // 初始化重新登录按钮
        initReloginButtons();
        
        // 为"前往帖子审核页面"按钮添加点击事件
        const articleAuditBtn = document.querySelector('a[href="7 judging.html"]');
        if (articleAuditBtn) {
            articleAuditBtn.addEventListener('click', async function(e) {
                e.preventDefault();
                await loadNextPendingArticle();
            });
        }
        
        console.log('审计页面初始化完成');
    } catch (error) {
        console.error('审计页面初始化错误:', error);
        alert('页面加载出错，请刷新重试');
    }
});

// 加载下一篇待审核文章
async function loadNextPendingArticle() {
    try {
        const response = await fetch(`${window.location.origin}/api/admin/articles/pending`, {
            headers: {
                'Authorization': `Bearer ${sessionStorage.getItem('auth_token')}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success && data.articles && data.articles.length > 0) {
            const nextArticle = data.articles[0];
            window.location.href = `7 judging.html?id=${nextArticle.id}`;
        } else {
            alert('当前没有待审核的文章');
        }
    } catch (error) {
        console.error('加载待审核文章失败:', error);
        alert('网络错误，请检查您的连接');
    }
}

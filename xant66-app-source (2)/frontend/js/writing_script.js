// 导入退出登录功能
import { initReloginButtons } from './auth.js';

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', function() {
    // 初始化重新登录按钮的事件处理
    initReloginButtons();
    
    // 添加页面加载日志
    console.log('%c[页面加载] 写作页面已加载完成', 'color: blue; font-weight: bold');
    
    // 获取表单元素
    const messageForm = document.getElementById('messageForm');
    const titleInput = document.getElementById('name');
    const categoryInput = document.getElementById('category');
    const contentInput = document.getElementById('content');
    const messagesDiv = document.getElementById('messages');
    const submitBtn = messageForm.querySelector('button[type="submit"]');
    
    // 检查元素是否存在
    if (!messageForm || !titleInput || !categoryInput || !contentInput || !messagesDiv || !submitBtn) {
        console.error('[页面初始化错误] 无法找到必要的HTML元素');
        showMessage('页面加载异常，请刷新页面重试', 'error');
        return;
    }
    
    console.log('[页面初始化] 所有必要的HTML元素已成功获取');
    
    // 日志记录函数
    function logAction(level, action, details) {
        const timestamp = new Date().toISOString();
        const logMessage = `[${timestamp}] [${level}] ${action}`;
        
        if (details) {
            console.log(logMessage, details);
        } else {
            console.log(logMessage);
        }
    }
    
    // 提交文章的函数
    async function submitArticle(e) {
        e.preventDefault(); // 阻止表单默认提交
        
        // 获取表单数据
        const title = titleInput.value.trim();
        const content = contentInput.value.trim();
        const category = categoryInput.value;
        
        logAction('debug', '开始提交文章', { title, category, contentLength: content.length });
        
        // 表单验证
        if (!title) {
            showMessage('文章标题不能为空', 'error');
            logAction('warning', '文章提交失败：标题为空');
            return;
        }
        
        if (!content) {
            showMessage('文章内容不能为空', 'error');
            logAction('warning', '文章提交失败：内容为空');
            return;
        }
        
        if (!category) {
            showMessage('请选择文章分类', 'error');
            logAction('warning', '文章提交失败：分类未选择');
            return;
        }
        
        // 限制长度
        if (title.length > 200) {
            showMessage('文章标题不能超过200个字符', 'error');
            logAction('warning', '文章提交失败：标题过长', { length: title.length });
            return;
        }
        
        if (content.length > 10000) {
            showMessage('文章内容不能超过10000个字符', 'error');
            logAction('warning', '文章提交失败：内容过长', { length: content.length });
            return;
        }
        
        // 显示加载状态
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '🚀 提交中...';
        
        try {
            logAction('info', '发送文章提交请求', { title, category });
            
            // 检查token是否存在
            const token = sessionStorage.getItem('auth_token');
            if (!token) {
                throw new Error('用户未登录，请重新登录');
            }
            
            const response = await fetch(`${window.location.origin}/api/articles/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ title, content, category })
            });
            
            logAction('debug', '收到服务器响应', { status: response.status });
            
            // 先检查响应状态
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `服务器响应错误: ${response.status}`);
            }
            
            // 解析JSON响应
            const result = await response.json();
            logAction('info', '文章提交成功', { articleId: result.article_id });
            showMessage(result.message || '文章提交成功，等待审核', 'success');
            
            // 清空表单
            titleInput.value = '';
            contentInput.value = '';
            categoryInput.value = '';
            
            // 延迟后跳转到正确的页面
            setTimeout(() => {
                window.location.href = '5 welcome.html';
            }, 2000);
        } catch (error) {
            logAction('error', '文章提交失败', { error: error.message });
            showMessage(`提交失败：${error.message}`, 'error');
        } finally {
            // 恢复按钮状态
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        }
    }
    
    // 显示消息的函数
    function showMessage(text, type = 'info') {
        const messageElement = document.createElement('div');
        messageElement.className = `message message-${type}`;
        messageElement.textContent = text;
        
        messagesDiv.appendChild(messageElement);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
        // 3秒后自动移除消息
        setTimeout(() => {
            messageElement.style.opacity = '0';
            setTimeout(() => messageElement.remove(), 500);
        }, 3000);
    }
    
    // 添加表单提交事件监听
    messageForm.addEventListener('submit', submitArticle);
    logAction('INFO', '表单提交事件监听器已注册');
});

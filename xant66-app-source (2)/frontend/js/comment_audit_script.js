// API配置
const API_BASE_URL = window.location.origin + '/api';

// 获取认证token
function getAuthToken() {
    return sessionStorage.getItem('auth_token') || localStorage.getItem('auth_token');
}

// 显示通知消息
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-500 text-white' :
        type === 'error' ? 'bg-red-500 text-white' :
        type === 'warning' ? 'bg-yellow-500 text-black' :
        'bg-blue-500 text-white'
    }`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// 加载待审核评论列表
async function loadPendingComments() {
    try {
        const token = getAuthToken();
        if (!token) {
            showNotification('请先登录', 'error');
            window.location.href = '4 login.html';
            return;
        }

        const response = await fetch(`${API_BASE_URL}/comments/pending`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (response.ok && data.status === 'success') {
            displayComments(data.comments);
            showNotification(`加载了 ${data.count} 条待审核评论`, 'success');
        } else {
            throw new Error(data.detail || '加载评论失败');
        }
    } catch (error) {
        console.error('加载待审核评论失败:', error);
        showNotification(error.message || '加载评论失败', 'error');
        
        // 如果是权限问题，跳转到登录页面
        if (error.message.includes('权限') || error.message.includes('登录')) {
            setTimeout(() => {
                window.location.href = '4 login.html';
            }, 2000);
        }
    }
}

// 显示评论列表
function displayComments(comments) {
    const container = document.querySelector('.space-y-4');
    
    if (!container) {
        console.error('找不到评论容器');
        return;
    }

    // 清空现有内容
    container.innerHTML = '';

    if (comments.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8">
                <p class="text-gray-500 text-lg">暂无待审核评论</p>
            </div>
        `;
        return;
    }

    // 生成评论HTML
    comments.forEach(comment => {
        const commentElement = document.createElement('div');
        commentElement.className = 'comment-item';
        commentElement.dataset.commentId = comment.id;
        
        commentElement.innerHTML = `
            <div class="mb-4">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <span class="font-semibold text-gray-800">${comment.username}</span>
                        <span class="text-gray-500 text-sm ml-2">评论于文章: ${comment.article_title}</span>
                    </div>
                    <span class="text-gray-400 text-sm">${formatDate(comment.created_at)}</span>
                </div>
                <p class="text-gray-600 mb-4 bg-gray-50 p-3 rounded">${comment.content}</p>
                <div class="comment-actions">
                    <button class="approve-btn" data-comment-id="${comment.id}">通过</button>
                    <button class="reject-btn" data-comment-id="${comment.id}">拒绝</button>
                </div>
            </div>
        `;
        
        container.appendChild(commentElement);
    });

    // 重新绑定事件监听器
    bindCommentActions();
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// 绑定评论操作事件
function bindCommentActions() {
    console.log('开始绑定评论操作事件...');
    
    // 获取所有审核按钮
    const approveButtons = document.querySelectorAll('.approve-btn');
    const rejectButtons = document.querySelectorAll('.reject-btn');
    
    console.log(`找到 ${approveButtons.length} 个通过按钮`);
    console.log(`找到 ${rejectButtons.length} 个拒绝按钮`);
    
    // 添加通过按钮事件监听
    approveButtons.forEach((button, index) => {
        console.log(`绑定通过按钮 ${index + 1}:`, button);
        button.addEventListener('click', function(e) {
            console.log('通过按钮被点击!', e.target);
            e.preventDefault();
            e.stopPropagation();
            const commentId = this.dataset.commentId;
            console.log('评论ID:', commentId);
            handleCommentAudit(commentId, 'approve');
        });
    });
    
    // 添加拒绝按钮事件监听
    rejectButtons.forEach((button, index) => {
        console.log(`绑定拒绝按钮 ${index + 1}:`, button);
        button.addEventListener('click', function(e) {
            console.log('拒绝按钮被点击!', e.target);
            e.preventDefault();
            e.stopPropagation();
            const commentId = this.dataset.commentId;
            console.log('评论ID:', commentId);
            handleCommentAudit(commentId, 'reject');
        });
    });
    
    console.log('事件绑定完成');
}

// 处理评论审核
async function handleCommentAudit(commentId, action) {
    console.log(`开始处理评论审核: ID=${commentId}, 操作=${action}`);
    
    try {
        const token = getAuthToken();
        if (!token) {
            console.log('未找到认证token');
            showNotification('请先登录', 'error');
            return;
        }

        console.log('发送审核请求...');
        const response = await fetch(`${API_BASE_URL}/comments/${commentId}/audit`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: action })
        });

        console.log('收到响应:', response.status, response.statusText);
        const data = await response.json();
        console.log('响应数据:', data);

        if (response.ok && data.status === 'success') {
            // 找到对应的评论元素
            const commentItem = document.querySelector(`[data-comment-id="${commentId}"]`);
            
            if (commentItem) {
                // 视觉反馈
                const bgColor = action === 'approve' ? '#d1fae5' : '#fee2e2';
                commentItem.style.backgroundColor = bgColor;
                
                setTimeout(() => {
                    commentItem.style.opacity = '0';
                    setTimeout(() => {
                        commentItem.remove();
                        const actionText = action === 'approve' ? '通过' : '拒绝';
                        showNotification(`评论已${actionText}`, 'success');
                        
                        // 检查是否还有评论，如果没有则显示空状态
                        const remainingComments = document.querySelectorAll('.comment-item');
                        if (remainingComments.length === 0) {
                            const container = document.querySelector('.space-y-4');
                            container.innerHTML = `
                                <div class="text-center py-8">
                                    <p class="text-gray-500 text-lg">暂无待审核评论</p>
                                    <button onclick="loadPendingComments()" class="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">刷新</button>
                                </div>
                            `;
                        }
                    }, 300);
                }, 500);
            }
        } else {
            throw new Error(data.detail || data.message || '审核操作失败');
        }
    } catch (error) {
        console.error('审核评论失败:', error);
        showNotification(error.message || '审核操作失败', 'error');
    }
}

// 显示通知消息
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transition-all duration-300 transform translate-y-0 opacity-0`;
    
    // 设置不同类型的通知样式
    switch(type) {
        case 'success':
            notification.className += ' bg-green-500 text-white';
            break;
        case 'error':
            notification.className += ' bg-red-500 text-white';
            break;
        case 'info':
            notification.className += ' bg-blue-500 text-white';
            break;
        default:
            notification.className += ' bg-gray-700 text-white';
    }
    
    // 设置通知内容
    notification.textContent = message;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 显示通知
    setTimeout(() => {
        notification.style.transform = 'translateY(0)';
        notification.style.opacity = '1';
    }, 10);
    
    // 3秒后隐藏通知
    setTimeout(() => {
        notification.style.transform = 'translateY(20px)';
        notification.style.opacity = '0';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// 页面加载完成后执行初始化
document.addEventListener('DOMContentLoaded', function() {
    // 加载待审核评论
    loadPendingComments();
});
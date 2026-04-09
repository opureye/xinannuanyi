/**
 * 文章页面交互脚本
 * 处理文章展示、互动和用户关注等功能
 */

// 导入必要的模块
import { getArticle, updateArticleInteraction, getLoggedInUser, isFollowing, followUser, unfollowUser } from './api.js';
import { showNotification } from './utils.js';
import { initAIModule } from './sdk_utils.js';
import { initReloginButtons } from './auth.js';

// 切换关注状态
function toggleFollow(button) {
    // 从DOM中获取作者名称
    const authorLink = document.querySelector('.author-name');
    const authorName = authorLink ? authorLink.textContent.trim() : null;
    
    if (!authorName) {
        showNotification('无法获取作者信息', 'error');
        return;
    }
    
    if (button.textContent.includes('关注')) {
        button.textContent = '💔 取关';
        button.style.background = '#e74c3c';
        // 调用API来更新用户的关注状态
        followUser(authorName).then(success => {
            if (success) {
                showNotification(`已关注 ${authorName}`, 'success');
            } else {
                // 如果失败，恢复按钮状态
                button.textContent = '❤️ 关注';
                button.style.background = '#3498db';
            }
        });
    } else {
        button.textContent = '❤️ 关注';
        button.style.background = '#3498db';
        // 调用API来更新用户的关注状态
        unfollowUser(authorName).then(success => {
            if (success) {
                showNotification(`已取消关注 ${authorName}`, 'info');
            } else {
                // 如果失败，恢复按钮状态
                button.textContent = '💔 取关';
                button.style.background = '#e74c3c';
            }
        });
    }
}

// 加载文章内容
async function loadArticle() {
    // 获取 URL 参数
    const urlParams = new URLSearchParams(window.location.search);
    const articleId = urlParams.get('id');
    console.log('加载文章ID:', articleId);

    try {
        // 从API获取文章数据
        const data = await getArticle(articleId);
        const article = data.article;
        
        if (article) {
            const articleContainer = document.getElementById('article-container');
            
            // 格式化更新时间
            const updatedDate = new Date(article.updated_at).toLocaleDateString('zh-CN');
            
            // 检查当前登录用户是否已关注该作者
            let isFollowingAuthor = false;
            const loggedInUser = getLoggedInUser();
            if (loggedInUser && loggedInUser.username !== article.author) {
                isFollowingAuthor = await isFollowing(loggedInUser.username, article.author);
            }
            
            articleContainer.innerHTML = `
                <h1>${article.title}</h1>
                <div class="article-meta">最后更新：${updatedDate} | 作者：
                    <a href="17 hispace.html?username=${article.author}" class="author-name" style="color: #3498db; text-decoration: underline;">${article.author}</a>
                    ${loggedInUser && loggedInUser.username !== article.author ? 
                        `<a href="javascript:void(0);" class="follow-btn" onclick="toggleFollow(this)">${isFollowingAuthor ? '💔 取关' : '❤️ 关注'}</a>` : ''}
                </div>
                <div class="article-content">${article.content.replace(/\n/g, '<br>')}</div>
            `;
            
            // 更新详细举报按钮的链接，传递正确的文章ID
            const auditButton = document.querySelector('.audit-btn');
            if (auditButton) {
                auditButton.href = `18 complaint.html?id=${articleId}`;
            }
            
            // 更新互动计数
            document.getElementById('like-count').textContent = article.like_count || 0;
            document.getElementById('helpful-count').textContent = article.helpful_count || 0;
            document.getElementById('unhelpful-count').textContent = article.unhelpful_count || 0;
            document.getElementById('complain-count').textContent = article.complain_count || 0;
            
            // 加载用户对该文章的互动状态
            await loadUserInteractions(articleId);
        } else {
            // 显示文章不存在的信息
            document.getElementById('article-container').innerHTML = `
                <div class="error-message">
                    <h2>文章不存在</h2>
                    <p>抱歉，您请求的文章可能已被删除或暂时无法访问。</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('加载文章失败:', error);
        document.getElementById('article-container').innerHTML = `
            <div class="error-message">
                <h2>加载失败</h2>
                <p>无法加载文章内容，请稍后重试。</p>
            </div>
        `;
    }
}

// 切换点赞状态
async function toggleLike() {
    console.log('toggleLike函数被调用');
    
    const articleId = new URLSearchParams(window.location.search).get('id');
    const likeIcon = document.getElementById('like-icon');
    const likeCount = document.getElementById('like-count');
    
    console.log('文章ID:', articleId);
    console.log('点赞图标元素:', likeIcon);
    console.log('点赞数量元素:', likeCount);
    
    // 检查用户是否已登录
    const loggedInUser = getLoggedInUser();
    console.log('登录用户信息:', loggedInUser);
    
    if (!loggedInUser) {
        console.log('用户未登录，显示提示');
        showNotification('请先登录后再点赞', 'warning');
        return;
    }
    
    try {
        console.log('开始调用updateArticleInteraction');
        const result = await updateArticleInteraction(articleId, 'liked', 1);
        console.log('API调用结果:', result);
        
        if (result && result.status === 'success') {
            // 更新点赞图标和数量
            likeIcon.textContent = '❤️';
            likeCount.textContent = result.like_count;
            showNotification('点赞成功！', 'success');
        }
    } catch (error) {
        console.error('点赞操作失败:', error);
        showNotification('点赞失败，请稍后重试', 'error');
    }
}

// 标记为有帮助
async function markHelpful() {
    const articleId = new URLSearchParams(window.location.search).get('id');
    const helpfulIcon = document.getElementById('helpful-icon');
    const helpfulCount = document.getElementById('helpful-count');
    const unhelpfulIcon = document.getElementById('unhelpful-icon');
    const unhelpfulCount = document.getElementById('unhelpful-count');
    
    const value = helpfulIcon.textContent === '✅' ? 0 : 1;
    
    try {
        const result = await updateArticleInteraction(articleId, 'helpful', value);
        console.log('markHelpful API result:', result);
        
        if (result && result.status === 'success') {
            if (value === 1) {
                helpfulIcon.textContent = '✅';
                // 如果之前标记为没帮助，取消那个标记
                if (unhelpfulIcon.textContent === '❌') {
                    unhelpfulIcon.textContent = '❎';
                    await updateArticleInteraction(articleId, 'unhelpful', 0);
                }
            } else {
                helpfulIcon.textContent = '☑️';
            }
            helpfulCount.textContent = result.counts.helpful_count;
            unhelpfulCount.textContent = result.counts.unhelpful_count;
        }
    } catch (error) {
        console.error('标记有帮助操作失败:', error);
        showNotification('操作失败，请稍后重试', 'error');
    }
}

// 标记为没帮助
async function markUnhelpful() {
    const articleId = new URLSearchParams(window.location.search).get('id');
    const unhelpfulIcon = document.getElementById('unhelpful-icon');
    const unhelpfulCount = document.getElementById('unhelpful-count');
    const helpfulIcon = document.getElementById('helpful-icon');
    const helpfulCount = document.getElementById('helpful-count');
    
    const value = unhelpfulIcon.textContent === '❌' ? 0 : 1;
    
    try {
        const result = await updateArticleInteraction(articleId, 'unhelpful', value);
        console.log('markUnhelpful API result:', result);
        
        if (result && result.status === 'success') {
            if (value === 1) {
                unhelpfulIcon.textContent = '❌';
                // 如果之前标记为有帮助，取消那个标记
                if (helpfulIcon.textContent === '✅') {
                    helpfulIcon.textContent = '☑️';
                    await updateArticleInteraction(articleId, 'helpful', 0);
                }
            } else {
                unhelpfulIcon.textContent = '❎';
            }
            unhelpfulCount.textContent = result.counts.unhelpful_count;
            helpfulCount.textContent = result.counts.helpful_count;
        }
    } catch (error) {
        console.error('标记没帮助操作失败:', error);
        showNotification('操作失败，请稍后重试', 'error');
    }
}

// 举报文章
async function complainArticle() {
    const articleId = new URLSearchParams(window.location.search).get('id');
    const complainIcon = document.getElementById('complain-icon');
    const complainCount = document.getElementById('complain-count');
    
    // 在实际应用中，这里应该显示一个举报原因表单
    alert('感谢您的举报，我们会尽快处理！');
    
    // 由于我们没有为举报创建单独的API端点，这里仅更新UI
    const currentCount = parseInt(complainCount.textContent);
    complainCount.textContent = currentCount + 1;
    complainIcon.textContent = '🚨';
    
    // 在实际应用中，这里应该调用API来记录举报
}

// 加载用户对文章的互动状态
async function loadUserInteractions(articleId) {
    try {
        // 这里应该调用API来获取用户对文章的互动状态
        // 为了简化，这里我们先省略具体实现
        // const response = await fetch(`http://localhost:8000/api/article/${articleId}/interaction`, {
        //     method: 'GET',
        //     headers: {
        //         'Content-Type': 'application/json',
        //         'Authorization': `Bearer ${localStorage.getItem('sessionToken')}`
        //     }
        // });
        // 
        // if (response.ok) {
        //     const data = await response.json();
        //     // 更新UI显示用户的互动状态
        // }
    } catch (error) {
        console.error('加载用户互动状态失败:', error);
    }
}

// 评论相关功能
async function loadComments() {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const articleId = urlParams.get('id');
        
        if (!articleId) {
            console.error('文章ID不存在');
            return;
        }
        
        const response = await fetch(`${window.location.origin}/api/articles/${articleId}/comments`);
        
        if (response.ok) {
            const data = await response.json();
            displayComments(data.comments);
        } else {
            console.error('加载评论失败:', response.status);
            displayComments([]);
        }
    } catch (error) {
        console.error('加载评论时发生错误:', error);
        displayComments([]);
    }
}

function displayComments(comments) {
    const commentsList = document.getElementById('comments-list');
    
    if (!comments || comments.length === 0) {
        commentsList.innerHTML = '<div class="no-comments">暂无评论，快来发表第一条评论吧！</div>';
        return;
    }
    
    let commentsHTML = '';
    comments.forEach(comment => {
        const commentDate = new Date(comment.created_at).toLocaleString('zh-CN');
        // 获取点赞数量，如果没有则默认为0
        const likeCount = comment.like_count || 0;
        // 获取用户是否已点赞，如果没有则默认为false
        const isLiked = comment.is_liked || false;
        
        commentsHTML += `
            <div class="comment-item" data-comment-id="${comment.id}">
                <div class="comment-header">
                    <span class="comment-author">${comment.username}</span>
                    <span class="comment-time">${commentDate}</span>
                </div>
                <div class="comment-content">${comment.content}</div>
                <div class="comment-actions">
                    <button class="comment-like-btn ${isLiked ? 'liked' : ''}" onclick="toggleCommentLike(${comment.id})">
                        <span>👍</span>
                        <span>${isLiked ? '已点赞' : '点赞'}</span>
                    </button>
                    <span class="like-count">${likeCount} 个赞</span>
                </div>
            </div>
        `;
    });
    
    commentsList.innerHTML = commentsHTML;
}

async function submitComment() {
    console.log('submitComment函数被调用');
    try {
        const commentInput = document.getElementById('comment-input');
        const submitBtn = document.getElementById('submit-comment-btn');
        const content = commentInput.value.trim();
        console.log('评论内容:', content);
        
        if (!content) {
            showNotification('评论内容不能为空', 'error');
            return;
        }
        
        const urlParams = new URLSearchParams(window.location.search);
        const articleId = urlParams.get('id');
        
        if (!articleId) {
            showNotification('文章ID不存在', 'error');
            return;
        }
        
        // 检查登录状态
        const token = sessionStorage.getItem('auth_token');
        console.log('获取到的token:', token);
        if (!token) {
            showNotification('请先登录后再发表评论', 'error');
            return;
        }
        
        // 禁用提交按钮
        submitBtn.disabled = true;
        submitBtn.textContent = '提交中...';
        
        console.log('准备发送API请求，URL:', `${window.location.origin}/api/articles/${articleId}/comments`);
        console.log('请求数据:', { content: content });
        
        const response = await fetch(`${window.location.origin}/api/articles/${articleId}/comments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ content: content })
        });
        
        console.log('API响应状态:', response.status);
        console.log('API响应:', response);
        
        if (response.ok) {
            const data = await response.json();
            console.log('API响应数据:', data);
            showNotification('评论提交成功，等待审核', 'success');
            commentInput.value = '';
            updateCharCount();
            // 重新加载评论列表
            loadComments();
        } else {
            const errorData = await response.json().catch(() => ({}));
            console.log('API错误响应:', errorData);
            const errorMessage = errorData.detail || '评论提交失败';
            showNotification(errorMessage, 'error');
        }
    } catch (error) {
        console.error('提交评论时发生错误:', error);
        showNotification('评论提交失败，请稍后重试', 'error');
    } finally {
        // 恢复提交按钮
        const submitBtn = document.getElementById('submit-comment-btn');
        submitBtn.disabled = false;
        submitBtn.textContent = '发表评论';
    }
}

async function toggleCommentLike(commentId) {
    try {
        const token = sessionStorage.getItem('auth_token');
        if (!token) {
            showNotification('请先登录后再点赞', 'error');
            return;
        }
        
        const response = await fetch(`${window.location.origin}/api/comments/${commentId}/like`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            showNotification(data.message, 'success');
            
            // 更新UI中的点赞按钮状态和点赞数量
            const likeBtn = document.querySelector(`[onclick="toggleCommentLike(${commentId})"]`);
            if (likeBtn) {
                // 更新按钮样式
                if (data.liked) {
                    likeBtn.classList.add('liked');
                    likeBtn.innerHTML = '👍 已点赞';
                } else {
                    likeBtn.classList.remove('liked');
                    likeBtn.innerHTML = '👍 点赞';
                }
                
                // 更新点赞数量显示
                const likeCountElement = likeBtn.parentElement.querySelector('.like-count');
                if (likeCountElement) {
                    likeCountElement.textContent = `${data.like_count} 个赞`;
                } else {
                    // 如果没有点赞数量元素，创建一个
                    const likeCountSpan = document.createElement('span');
                    likeCountSpan.className = 'like-count';
                    likeCountSpan.textContent = `${data.like_count} 个赞`;
                    likeBtn.parentElement.appendChild(likeCountSpan);
                }
            }
        } else {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.detail || '点赞失败';
            showNotification(errorMessage, 'error');
        }
    } catch (error) {
        console.error('点赞评论时发生错误:', error);
        showNotification('点赞失败，请稍后重试', 'error');
    }
}

function updateCharCount() {
    const commentInput = document.getElementById('comment-input');
    const charCount = document.querySelector('.char-count');
    
    if (commentInput && charCount) {
        const currentLength = commentInput.value.length;
        charCount.textContent = `${currentLength}/1000`;
        
        // 如果超过限制，改变颜色
        if (currentLength > 1000) {
            charCount.style.color = '#e74c3c';
        } else if (currentLength > 800) {
            charCount.style.color = '#f39c12';
        } else {
            charCount.style.color = '#666';
        }
    }
}

function initCommentFeatures() {
    // 初始化字符计数
    const commentInput = document.getElementById('comment-input');
    if (commentInput) {
        commentInput.addEventListener('input', updateCharCount);
        updateCharCount(); // 初始化显示
    }
    
    // 初始化提交按钮事件监听器
    const submitBtn = document.getElementById('submit-comment-btn');
    console.log('提交按钮元素:', submitBtn);
    if (submitBtn) {
        submitBtn.addEventListener('click', submitComment);
        console.log('评论提交按钮事件监听器已绑定');
    } else {
        console.error('未找到提交按钮元素');
    }
    
    // 加载评论列表
    loadComments();
}

// 页面加载完成后初始化
function initPage() {
    // 初始化重新登录按钮的事件处理
    initReloginButtons();
    
    // 加载文章内容
    loadArticle();
    
    // 初始化AI模块
    initAIModule();
    
    // 初始化评论功能
    initCommentFeatures();
}

// 页面加载完成后执行初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPage);
} else {
    initPage();
}

// 全局函数暴露，以便在HTML中直接调用
window.toggleFollow = toggleFollow;
window.toggleLike = toggleLike;
window.markHelpful = markHelpful;
window.markUnhelpful = markUnhelpful;
window.complainArticle = complainArticle;
window.toggleCommentLike = toggleCommentLike;

// 导入API函数
// 导入新增的getUserInfo函数
import { getLoggedInUser, getUserCollections, removeCollection, showNotification, getUserInfo, isFollowing, followUser, unfollowUser } from './api.js';

/**
 * 设置关注按钮功能
 */
function setupFollowButton() {
    const followBtn = document.querySelector('.follow-btn');
    if (followBtn) {
        followBtn.addEventListener('click', async function() {
            const urlParams = new URLSearchParams(window.location.search);
            const targetUsername = urlParams.get('username') || '默认用户名';
            
            await toggleFollow(this, targetUsername);
        });
    }
}

/**
 * 切换关注状态
 * @param {HTMLElement} button - 关注按钮元素
 * @param {string} targetUsername - 目标用户名
 */
async function toggleFollow(button, targetUsername) {
    if (button.textContent.includes('关注')) {
        // 切换为关注状态
        const success = await followUser(targetUsername);
        if (success) {
            button.textContent = '💔 取关';
            button.classList.add('following');
            showNotification(`已成功关注 ${targetUsername}`, 'success');
            
            // 模拟更新粉丝数
            updateFanCount(1);
        }
    } else {
        // 切换为未关注状态
        const success = await unfollowUser(targetUsername);
        if (success) {
            button.textContent = '❤️ 关注';
            button.classList.remove('following');
            showNotification('已取消关注', 'info');
            
            // 模拟更新粉丝数
            updateFanCount(-1);
        }
    }
}

/**
 * 加载用户信息
 */
async function loadUserInfo() {
    const urlParams = new URLSearchParams(window.location.search);
    const targetUsername = urlParams.get('username');
    const loggedInUser = getLoggedInUser();
    
    // 如果没有指定用户名，使用当前登录用户的用户名
    const username = targetUsername || (loggedInUser ? loggedInUser.username : '默认用户名');
    
    // 获取用户信息
    const userInfo = await getUserInfo(username);
    
    if (userInfo) {
        // 更新页面上的用户信息
        document.querySelector('.profile h2').textContent = userInfo.username || username;
        document.querySelector('.profile p:nth-of-type(1)').textContent = userInfo.bio || '暂无简介';
        document.getElementById('current-level-info').textContent = `当前等级：${userInfo.level || 1}，经验值：${userInfo.exp || 0}`;
        
        // 更新个人成就信息
        const achievementsList = document.querySelector('.achievements-list');
        if (achievementsList) {
            achievementsList.innerHTML = `
                <li class="text-gray-700">发帖数量：${userInfo.posts_count || 0} 篇</li>
                <li class="text-gray-700">粉丝数：${userInfo.followers_count || 0}个</li>
                <li class="text-gray-700">总点赞数：${userInfo.likes_received || 0}个</li>
                <li class="text-gray-700">被标记为有帮助的帖子数：${userInfo.helpful_posts || 0}篇</li>
            `;
        }
        
        // 检查是否为当前登录用户查看自己的主页
        const followBtn = document.querySelector('.follow-btn');
        if (followBtn && loggedInUser && loggedInUser.username !== username) {
            // 检查是否已关注
            const following = await isFollowing(loggedInUser.username, username);
            if (following) {
                followBtn.textContent = '💔 取关';
                followBtn.classList.add('following');
            } else {
                followBtn.textContent = '❤️ 关注';
                followBtn.classList.remove('following');
            }
        } else if (followBtn) {
            // 如果是查看自己的主页，隐藏关注按钮
            followBtn.style.display = 'none';
        }
        
        // 更新页面标题
        document.title = `信安暖驿 - ${userInfo.username || username}的主页`;
    }
}

/**
 * 初始化页面功能
 */
async function initPage() {
    // 初始化Coze SDK
    initCozeSDK();
    
    // 设置关注按钮
    setupFollowButton();
    
    // 设置平滑滚动
    setupSmoothScroll();
    
    // 添加返回顶部按钮
    addBackToTopButton();
    
    // 增强交互体验
    enhanceInteractions();
    
    // 加载用户信息
    await loadUserInfo();
    
    // 加载用户收藏数据
    loadUserCollections();
}

/**
 * 更新粉丝数量
 * @param {number} change - 变化量（正数增加，负数减少）
 */
function updateFanCount(change) {
    const achievementsList = document.querySelector('.achievements-list');
    if (achievementsList) {
        const fanCountItem = Array.from(achievementsList.children).find(item => 
            item.textContent.includes('粉丝数')
        );
        
        if (fanCountItem) {
            const currentCount = parseInt(fanCountItem.textContent.match(/\d+/)[0]);
            const newCount = currentCount + change;
            fanCountItem.textContent = `粉丝数：${newCount}个`;
        }
    }
}

/**
 * 设置平滑滚动效果
 */
function setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
}

/**
 * 添加返回顶部按钮
 */
function addBackToTopButton() {
    const backToTopButton = document.createElement('button');
    backToTopButton.textContent = '↑';
    backToTopButton.id = 'backToTop';
    backToTopButton.style.position = 'fixed';
    backToTopButton.style.bottom = '30px';
    backToTopButton.style.right = '30px';
    backToTopButton.style.width = '50px';
    backToTopButton.style.height = '50px';
    backToTopButton.style.borderRadius = '50%';
    backToTopButton.style.backgroundColor = '#2A9D8F';
    backToTopButton.style.color = 'white';
    backToTopButton.style.border = 'none';
    backToTopButton.style.fontSize = '24px';
    backToTopButton.style.cursor = 'pointer';
    backToTopButton.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
    backToTopButton.style.opacity = '0';
    backToTopButton.style.transition = 'opacity 0.3s, transform 0.3s';
    backToTopButton.style.transform = 'translateY(20px)';
    backToTopButton.style.zIndex = '999';
    
    document.body.appendChild(backToTopButton);
    
    // 滚动事件监听
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopButton.style.opacity = '1';
            backToTopButton.style.transform = 'translateY(0)';
        } else {
            backToTopButton.style.opacity = '0';
            backToTopButton.style.transform = 'translateY(20px)';
        }
    });
    
    // 返回顶部点击事件
    backToTopButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

/**
 * 显示通知信息
 * @param {string} message - 通知消息
 * @param {string} type - 通知类型（success, error, info）
 */
function showNotification(message, type = 'info') {
    // 检查是否已存在通知元素
    let notification = document.getElementById('notification');
    if (notification) {
        document.body.removeChild(notification);
    }
    
    // 创建新的通知元素
    notification = document.createElement('div');
    notification.id = 'notification';
    notification.textContent = message;
    
    // 设置基础样式
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.left = '50%';
    notification.style.transform = 'translateX(-50%)';
    notification.style.padding = '15px 30px';
    notification.style.borderRadius = '25px';
    notification.style.color = 'white';
    notification.style.fontWeight = '500';
    notification.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.2)';
    notification.style.zIndex = '9999';
    notification.style.opacity = '0';
    notification.style.transition = 'opacity 0.3s, transform 0.3s';
    notification.style.transform = 'translate(-50%, -20px)';
    
    // 根据类型设置不同背景色
    switch(type) {
        case 'success':
            notification.style.backgroundColor = '#27ae60';
            break;
        case 'error':
            notification.style.backgroundColor = '#e74c3c';
            break;
        case 'info':
        default:
            notification.style.backgroundColor = '#3498db';
            break;
    }
    
    document.body.appendChild(notification);
    
    // 显示通知
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translate(-50%, 0)';
    }, 10);
    
    // 3秒后隐藏通知
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translate(-50%, -20px)';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

/**
 * 加载用户收藏数据
 */
async function loadUserCollections() {
    const user = getLoggedInUser();
    if (!user) {
        showNotification('请先登录以查看收藏内容', 'info');
        return;
    }
    
    try {
        // 获取收藏列表容器
        const collectionsContainer = document.querySelector('.collections-list');
        if (!collectionsContainer) {
            console.error('未找到收藏列表容器');
            return;
        }
        
        // 清空现有内容
        collectionsContainer.innerHTML = '<div class="loading">加载中...</div>';
        
        // 获取用户收藏数据
        const collections = await getUserCollections(user.username);
        
        // 清空加载提示
        collectionsContainer.innerHTML = '';
        
        if (collections.length === 0) {
            // 显示空状态
            collectionsContainer.innerHTML = '<div class="empty-collection">暂无收藏内容</div>';
            return;
        }
        
        // 渲染收藏列表
        collections.forEach(collection => {
            const collectionItem = document.createElement('div');
            collectionItem.className = 'collection-item';
            collectionItem.dataset.id = collection.id;
            
            // 构建收藏项HTML结构
            collectionItem.innerHTML = `
                <h4>${collection.title}</h4>
                <p>${collection.description}</p>
                <div class="collection-meta">
                    <span class="collect-time">${new Date(collection.collect_time).toLocaleString()}</span>
                    <button class="uncollect-btn" title="取消收藏">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                        </svg>
                    </button>
                </div>
            `;
            
            // 添加取消收藏按钮事件
            const uncollectBtn = collectionItem.querySelector('.uncollect-btn');
            uncollectBtn.addEventListener('click', async function(e) {
                e.stopPropagation();
                await handleUncollect(parseInt(collectionItem.dataset.id), collectionItem);
            });
            
            collectionsContainer.appendChild(collectionItem);
        });
        
        // 增强收藏项交互体验
        enhanceInteractions();
    } catch (error) {
        console.error('加载收藏数据失败:', error);
        showNotification('加载收藏数据失败，请稍后重试', 'error');
    }
}

/**
 * 处理取消收藏操作
 * @param {number} articleId - 文章ID
 * @param {HTMLElement} element - 收藏项元素
 */
async function handleUncollect(articleId, element) {
    try {
        // 添加删除动画
        element.style.transition = 'all 0.3s ease';
        element.style.opacity = '0';
        element.style.height = '0';
        element.style.marginBottom = '0';
        element.style.paddingTop = '0';
        element.style.paddingBottom = '0';
        element.style.overflow = 'hidden';
        
        // 等待动画完成后执行取消收藏
        setTimeout(async () => {
            const success = await removeCollection(articleId);
            if (success) {
                // 从DOM中移除元素
                if (element.parentNode) {
                    element.parentNode.removeChild(element);
                }
                
                // 检查是否还有收藏项
                const collectionsContainer = document.querySelector('.collections-list');
                if (collectionsContainer && collectionsContainer.children.length === 0) {
                    collectionsContainer.innerHTML = '<div class="empty-collection">暂无收藏内容</div>';
                }
                
                showNotification('已取消收藏', 'success');
            } else {
                showNotification('取消收藏失败，请稍后重试', 'error');
                // 恢复元素样式
                element.style.opacity = '1';
                element.style.height = 'auto';
                element.style.marginBottom = '';
                element.style.paddingTop = '';
                element.style.paddingBottom = '';
            }
        }, 300);
    } catch (error) {
        console.error('取消收藏失败:', error);
        showNotification('取消收藏失败，请稍后重试', 'error');
        // 恢复元素样式
        element.style.opacity = '1';
        element.style.height = 'auto';
        element.style.marginBottom = '';
        element.style.paddingTop = '';
        element.style.paddingBottom = '';
    }
}

// 增强帖子和收藏项的交互体验
function enhanceInteractions() {
    const interactiveItems = document.querySelectorAll('.post, .collection-item');
    
    interactiveItems.forEach(item => {
        // 添加悬停动画
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.1)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.05)';
        });
        
        // 添加点击效果
        item.addEventListener('click', function(e) {
            // 如果点击的是链接或按钮，则不触发卡片点击事件
            if (e.target.closest('a') || e.target.closest('button')) {
                return;
            }
            
            // 这里可以添加点击卡片的逻辑，例如展开详情等
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = 'translateY(-5px)';
            }, 100);
        });
    });
}

/**
 * 初始化页面功能
 */
function initPage() {
    // 初始化Coze SDK
    initCozeSDK();
    
    // 设置关注按钮
    setupFollowButton();
    
    // 设置平滑滚动
    setupSmoothScroll();
    
    // 添加返回顶部按钮
    addBackToTopButton();
    
    // 增强交互体验
    enhanceInteractions();
    
    // 加载用户收藏数据
    loadUserCollections();
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', initPage);
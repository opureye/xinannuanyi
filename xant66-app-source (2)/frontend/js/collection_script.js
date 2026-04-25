// 导入共享的SDK工具模块
import { getLoggedInUser, getUserCollections, removeCollection } from './api.js';

/**
 * 显示通知消息
 * @param {string} message - 通知消息内容
 * @param {string} type - 通知类型：'info', 'success', 'error', 'warning'
 */
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `fixed bottom-4 right-4 p-4 rounded-lg shadow-lg z-50 max-w-xs transition-all duration-300 ease-in-out transform translate-y-20 opacity-0`;
    
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
 * 初始化收藏页面交互
 */
function initCollectionPage() {
    // 为收藏列表项添加交互效果
    const collectionItems = document.querySelectorAll('.collection-list li');
    collectionItems.forEach((item, index) => {
        // 添加进入动画延迟，创造级联效果
        item.style.opacity = '0';
        item.style.transform = 'translateY(20px)';
        item.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        
        setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
        }, 100 * index);
        
        // 添加点击事件
        item.addEventListener('click', function(e) {
            // 如果点击的是取消收藏按钮，处理取消收藏
            if (e.target.classList.contains('uncollect-btn') || e.target.closest('.uncollect-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const articleId = parseInt(this.dataset.articleId);
                handleUncollect(articleId, this);
                return;
            }
            
            // 如果点击的是链接，让链接正常工作
            if (e.target.tagName === 'A' || e.target.closest('a')) {
                const linkText = e.target.textContent.trim() || e.target.closest('a').textContent.trim();
                showNotification(`正在跳转到: ${linkText}`, 'info');
            }
        });
    });
    
    // 添加页面加载完成的通知
    showNotification('收藏页面加载完成', 'success');
}

/**
 * 处理取消收藏操作
 * @param {number} articleId - 文章ID
 * @param {HTMLElement} listItem - 列表项元素
 */
async function handleUncollect(articleId, listItem) {
    try {
        // 显示加载状态
        listItem.classList.add('opacity-50');
        
        // 调用API取消收藏
        const success = await removeCollection(articleId);
        
        if (success) {
            // 从DOM中移除该收藏项，并添加淡出动画
            listItem.style.transition = 'opacity 0.3s, transform 0.3s';
            listItem.style.opacity = '0';
            listItem.style.transform = 'translateX(20px)';
            
            setTimeout(() => {
                listItem.remove();
                
                // 检查是否还有收藏项
                const remainingItems = document.querySelectorAll('.collection-list li');
                if (remainingItems.length === 0) {
                    // 显示空状态
                    const collectionList = document.querySelector('.collection-list');
                    collectionList.innerHTML = '<li class="text-gray-500 italic text-center">暂无收藏内容</li>';
                }
            }, 300);
            
            showNotification('已取消收藏', 'success');
        } else {
            showNotification('取消收藏失败，请稍后再试', 'error');
        }
    } catch (error) {
        console.error('取消收藏时出错:', error);
        showNotification('取消收藏失败：' + error.message, 'error');
    } finally {
        listItem.classList.remove('opacity-50');
    }
}

/**
 * 加载用户收藏
 */
// 修复API调用问题并移除重复的函数定义

// 移除重复的initCollectionPage函数定义

// 修复API调用，确保正确引用api对象
async function loadUserCollections() {
    try {
        const user = await getLoggedInUser();
        if (!user) {
            showNotification('用户未登录', 'error');
            window.location.href = '4 login.html';
            return;
        }
        
        const collectionsContainer = document.querySelector('.collection-list');
        if (collectionsContainer) {
            collectionsContainer.innerHTML = '<li class="text-gray-500 italic text-center py-8">加载收藏中...</li>';
        }
        
        const result = await getUserCollections(user.username);
        const collections = Array.isArray(result) ? result : (result.collections || []);
        
        if (collections.length === 0) {
            showNotification('暂无收藏的帖子', 'info');
        }
        
        renderCollections(collections);
    } catch (error) {
        console.error('加载收藏失败:', error);
        showNotification('加载收藏失败，请稍后重试', 'error');
    }
}

// 确保createCollectionItem函数中的API调用正确
function createCollectionItem(collection) {
    const li = document.createElement('li');
    li.className = 'collection-item mb-4 p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow';
    const articleId = collection.article_id || collection.item_id || collection.id;
    li.dataset.articleId = articleId;
    
    const articleLink = document.createElement('a');
    articleLink.href = `6 article.html?id=${articleId}`;
    articleLink.className = 'flex items-start justify-between w-full text-gray-800';
    
    // 帖子信息部分
    const contentDiv = document.createElement('div');
    contentDiv.className = 'flex-1 min-w-0 mr-4';
    
    const titleSpan = document.createElement('span');
    titleSpan.className = 'font-medium inline-block mb-1 truncate';
    titleSpan.textContent = collection.title || '无标题帖子';
    
    const metaDiv = document.createElement('div');
    metaDiv.className = 'text-xs text-gray-500 flex items-center';
    
    const authorSpan = document.createElement('span');
    authorSpan.className = 'flex items-center';
    authorSpan.innerHTML = `<i class="fas fa-user mr-1"></i> ${collection.author || '未知作者'}`;
    
    const categorySpan = document.createElement('span');
    categorySpan.className = 'mx-2';
    categorySpan.textContent = '•';
    
    const dateSpan = document.createElement('span');
    dateSpan.className = 'flex items-center';
    dateSpan.innerHTML = `<i class="fas fa-calendar-alt mr-1"></i> ${formatDate(collection.created_at)}`;
    
    const likeSpan = document.createElement('span');
    likeSpan.className = 'mx-2';
    likeSpan.textContent = '•';
    
    const likesSpan = document.createElement('span');
    likesSpan.className = 'flex items-center';
    likesSpan.innerHTML = `<i class="fas fa-thumbs-up mr-1"></i> ${collection.likes || 0}`;
    
    metaDiv.appendChild(authorSpan);
    metaDiv.appendChild(categorySpan);
    metaDiv.appendChild(dateSpan);
    metaDiv.appendChild(likeSpan);
    metaDiv.appendChild(likesSpan);
    
    contentDiv.appendChild(titleSpan);
    contentDiv.appendChild(metaDiv);
    
    // 操作按钮部分
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'flex items-center';
    
    const viewButton = document.createElement('button');
    viewButton.className = 'view-btn p-2 text-blue-600 hover:text-blue-800 mr-2';
    viewButton.innerHTML = '<i class="fas fa-eye"></i>';
    viewButton.title = '查看帖子';
    viewButton.addEventListener('click', (e) => {
        e.stopPropagation();
        window.location.href = `6 article.html?id=${articleId}`;
    });
    
    const removeButton = document.createElement('button');
    removeButton.className = 'remove-btn p-2 text-red-500 hover:text-red-700';
    removeButton.innerHTML = '<i class="fas fa-bookmark"></i>';
    removeButton.title = '取消收藏';
    removeButton.addEventListener('click', async (e) => {
        e.stopPropagation();
        
        if (confirm('确定要取消收藏这篇帖子吗？')) {
            try {
                const success = await removeCollection(articleId);
                if (success) {
                    showNotification('取消收藏成功', 'success');
                    li.remove();
                    
                    // 检查是否还有收藏项，如果没有则显示空状态
                    const collectionList = document.querySelector('.collection-list');
                    if (collectionList && collectionList.children.length === 0) {
                        renderEmptyCollection();
                    }
                } else {
                    showNotification('取消收藏失败，请稍后重试', 'error');
                }
            } catch (error) {
                console.error('取消收藏失败:', error);
                showNotification('操作失败，请稍后重试', 'error');
            }
        }
    });
    
    actionsDiv.appendChild(viewButton);
    actionsDiv.appendChild(removeButton);
    
    articleLink.appendChild(contentDiv);
    articleLink.appendChild(actionsDiv);
    
    li.appendChild(articleLink);
    
    return li;
}

function renderEmptyCollection() {
    const collectionList = document.querySelector('.collection-list');
    if (!collectionList) return;
    collectionList.innerHTML = `
        <li class="empty-state collection-empty">
            <i class="fa-regular fa-bookmark"></i>
            <h3>还没有收藏内容</h3>
            <p>看到有价值的互助帖子后，点收藏就能在这里快速找回。</p>
            <a href="5 welcome.html" class="btn">去论坛看看</a>
        </li>
    `;
}

function renderCollections(collections) {
    const collectionList = document.querySelector('.collection-list');
    if (!collectionList) return;

    collectionList.innerHTML = '';
    if (!collections || collections.length === 0) {
        renderEmptyCollection();
        return;
    }

    collections.forEach((collection) => {
        collectionList.appendChild(createCollectionItem(collection));
    });
}

/**
 * 格式化日期
 */
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
}

/**
 * 页面初始化
 */
function initCollectionPage() {
    loadUserCollections();
    addSmoothScroll();
    markCurrentNavButton();
}

/**
 * 标记当前导航按钮
 */
function markCurrentNavButton() {
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(button => {
        if (button.getAttribute('href') === '15 collection.html') {
            button.classList.add('active');
        }
    });
}

/**
 * 添加平滑滚动
 */
function addSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
}

// 初始化页面
window.addEventListener('DOMContentLoaded', initCollectionPage);
// 导入所需模块（必须在文件最开始）
import { apiRequest } from './api.js';
import { showNotification } from './utils.js';

const DEFAULT_AVATAR = 'assets/default-avatar.svg';

/**
 * 初始化页面
 */
function initPage() {
    loadUserData();
    addSmoothScroll();
    markCurrentNavButton();
    setupProfileEditor();
    
    // 帖子卡片点击事件
    document.querySelectorAll('.post').forEach(card => {
        card.addEventListener('click', () => {
            const postId = card.getAttribute('data-id');
            if (postId) {
                window.location.href = `6 article.html?id=${postId}`;
            }
        });
    });
}

/**
 * 加载用户数据
 */
async function loadUserData() {
    try {
        const token = sessionStorage.getItem('auth_token');
        if (!token) {
            showNotification('请先登录', 'error');
            window.location.href = '4 login.html';
            return;
        }
        
        const response = await apiRequest('/api/user/profile');
        
        // 从response.user_info中提取用户数据
        const userData = response.user_info || response;
        displayUserProfile(userData);
        updateLevelProgress(userData);
        displayUserAchievements(userData);
        await loadFollowingList(userData.username);
        await loadUserPosts(userData.username);
    } catch (error) {
        console.error('加载用户数据失败:', error);
        showNotification('加载个人信息失败，请稍后重试', 'error');
    }
}

/**
 * 显示用户个人资料
 */
function displayUserProfile(userData) {
    const avatar = document.querySelector('.avatar');
    if (avatar) {
        avatar.src = userData.avatar || DEFAULT_AVATAR;
        avatar.alt = userData.username || '用户头像';
        avatar.onerror = () => {
            avatar.onerror = null;
            avatar.src = DEFAULT_AVATAR;
        };
    }
    document.querySelector('h1.text-4xl.font-bold.mt-4').textContent = userData.username || '用户名称';
    
    // 查找并更新简介
    const bioElement = document.querySelector('p.text-gray-600.mt-2');
    if (bioElement) {
        bioElement.textContent = userData.bio || '这个人很懒，什么都没有留下。';
    }
}

/**
 * 更新等级进度
 */
function updateLevelProgress(userData) {
    const levelElement = document.getElementById('current-level-info');
    if (levelElement) {
        levelElement.textContent = `当前等级：${userData.level || 1}，经验值：${userData.exp || 0}`;
    }
}

/**
 * 显示用户成就
 */
function displayUserAchievements(userData) {
    // 这里可以添加显示用户成就的代码
    console.log('显示用户成就:', userData);
}

/**
 * 加载关注列表
 */
async function loadFollowingList(username) {
    try {
        const response = await apiRequest(`/api/user/${username}/following`);
        console.log('关注列表:', response);
        renderFollowingList(response || []);
    } catch (error) {
        console.error('加载关注列表失败:', error);
        showNotification('加载关注列表失败', 'error');
        renderFollowingList([]);
    }
}

/**
 * 加载用户帖子
 */
async function loadUserPosts(username) {
    try {
        // 使用正确的API端点获取当前用户的帖子
        const response = await apiRequest('/api/user/posts');
        renderUserPosts(response.posts || []);
    } catch (error) {
        console.error('加载用户帖子失败:', error);
        showNotification('加载用户帖子失败', 'error');
        // 在出错时显示空状态
        renderUserPosts([]);
    }
}

/**
 * 添加平滑滚动
 */
function addSmoothScroll() {
    // 为所有内部链接添加平滑滚动
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
}

/**
 * 标记当前导航按钮
 */
function markCurrentNavButton() {
    // 获取当前页面的文件名
    const currentPage = window.location.pathname.split('/').pop();
    
    // 查找对应的导航按钮并添加活动状态
    document.querySelectorAll('.nav-button').forEach(button => {
        const href = button.getAttribute('href');
        if (href && href.includes(currentPage)) {
            button.classList.add('active');
        }
    });
}

/**
 * 渲染关注列表
 */
function renderFollowingList(followingList) {
    const followingContainer = document.getElementById('following-list');
    if (!followingContainer) return;
    
    // 清空容器
    followingContainer.innerHTML = '';
    
    if (!followingList || followingList.length === 0) {
        const emptyMessage = document.createElement('div');
        emptyMessage.className = 'text-gray-500 text-center py-8';
        emptyMessage.innerHTML = `
            <div class="empty-state">
                <p>暂无关注列表</p>
            </div>
        `;
        followingContainer.appendChild(emptyMessage);
        return;
    }
    
    // 创建关注列表
    followingList.forEach((user, index) => {
        const userElement = createFollowingUserElement(user);
        // 添加动画延迟
        userElement.style.animationDelay = `${index * 0.1}s`;
        userElement.style.animation = 'fadeInUp 0.5s ease-out forwards';
        followingContainer.appendChild(userElement);
    });
}

/**
 * 创建关注用户元素
 */
function createFollowingUserElement(user) {
    const userDiv = document.createElement('div');
    userDiv.className = 'following-user';
    
    // 处理头像URL
    const avatarUrl = user.avatar || DEFAULT_AVATAR;
    
    // 处理关注时间
    const followedTime = user.followed_at ? formatDate(user.followed_at) : '未知时间';
    
    userDiv.innerHTML = `
        <div class="flex">
            <img src="${avatarUrl}" 
                 alt="${user.username || '用户'}" 
                 class="user-avatar"
                 loading="lazy"
                 onerror="this.src='${DEFAULT_AVATAR}'">
            <div class="flex-1">
                <h3>${user.username || '未知用户'}</h3>
                <p>${user.bio || '这个用户很神秘，什么都没有留下~'}</p>
                <p>关注时间: ${followedTime}</p>
            </div>
            <a href="17 hispace.html?username=${encodeURIComponent(user.username || '')}" 
               class="view-profile-btn">
                <i class="fas fa-user"></i> 查看主页
            </a>
        </div>
    `;
    
    // 添加点击事件（除了按钮区域）
    userDiv.addEventListener('click', (e) => {
        // 如果点击的不是按钮，则跳转到用户主页
        if (!e.target.closest('.view-profile-btn')) {
            window.location.href = `17 hispace.html?username=${encodeURIComponent(user.username || '')}`;
        }
    });
    
    return userDiv;
}

/**
 * 渲染用户帖子
 */
function renderUserPosts(posts) {
    const postsContainer = document.querySelector('.posts');
    if (!postsContainer) return;
    
    // 保留标题，清空内容
    const title = postsContainer.querySelector('h2');
    postsContainer.innerHTML = '';
    if (title) {
        postsContainer.appendChild(title);
    }
    
    if (!posts || posts.length === 0) {
        const emptyMessage = document.createElement('div');
        emptyMessage.className = 'text-gray-500 text-center py-8';
        emptyMessage.textContent = '暂无发布的帖子';
        postsContainer.appendChild(emptyMessage);
        return;
    }
    
    posts.forEach(post => {
        const postElement = createPostElement(post);
        postsContainer.appendChild(postElement);
    });
}

/**
 * 创建帖子元素
 */
function createPostElement(post) {
    const postElement = document.createElement('div');
    postElement.className = 'post bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer';
    // 使用正确的字段名：post_id 或 id
    const postId = post.post_id || post.id;
    postElement.setAttribute('data-id', postId);
    
    postElement.innerHTML = `
        <h3 class="text-xl font-bold mb-2">${post.title}</h3>
        <p class="text-gray-700 mb-4">${post.content.substring(0, 100)}${post.content.length > 100 ? '...' : ''}</p>
        ${post.imageUrl ? `
        <div class="post-image-container mb-4">
            <img src="${post.imageUrl}" alt="${post.title}" class="w-full h-48 object-cover rounded" loading="lazy" onerror="this.src='assets/card-placeholder.svg'">
        </div>
        ` : ''}
        <div class="post-stats flex items-center text-sm text-gray-500">
            <i class="fa-solid fa-thumbs-up mr-1"></i>
            <span class="mr-4">${post.likes_count || post.likeCount || 0} 个赞</span>
            <i class="fa-solid fa-eye mr-1"></i>
            <span class="mr-4">${post.viewCount || 0} 次浏览</span>
            ${post.isHelpful ? `
            <i class="fa-solid fa-check text-green-500 mr-1"></i>
            <span class="text-green-500">有帮助</span>
            ` : ''}
        </div>
    `;
    
    // 添加点击事件
    postElement.addEventListener('click', () => {
        window.location.href = `6 article.html?id=${postId}`;
    });
    
    return postElement;
}

/**
 * 加载用户收藏
 */
async function loadUserCollections(username) {
    try {
        const response = await apiRequest(`/api/user/${username}/collections`);
        renderUserCollections(response.collections || []);
    } catch (error) {
        console.error('加载用户收藏失败:', error);
        showNotification('加载收藏失败，请稍后重试', 'error');
    }
}

/**
 * 渲染用户收藏
 */
function renderUserCollections(collections) {
    const collectionsContainer = document.querySelector('.collections');
    if (!collectionsContainer) return;
    
    // 保留标题，清空内容
    const title = collectionsContainer.querySelector('h2');
    collectionsContainer.innerHTML = '';
    if (title) {
        collectionsContainer.appendChild(title);
    }
    
    if (!collections || collections.length === 0) {
        const emptyMessage = document.createElement('div');
        emptyMessage.className = 'text-gray-500 text-center py-8';
        emptyMessage.textContent = '暂无收藏的帖子';
        collectionsContainer.appendChild(emptyMessage);
        return;
    }
    
    collections.forEach(collection => {
        const collectionElement = createCollectionElement(collection);
        collectionsContainer.appendChild(collectionElement);
    });
}

/**
 * 创建收藏元素
 */
function createCollectionElement(collection) {
    const collectionElement = document.createElement('div');
    collectionElement.className = 'collection-item bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer';
    collectionElement.setAttribute('data-id', collection.article_id);
    
    collectionElement.innerHTML = `
        <h3 class="text-xl font-bold mb-2">${collection.title}</h3>
        <p class="text-gray-700 mb-4">${collection.content ? collection.content.substring(0, 100) : ''}${collection.content && collection.content.length > 100 ? '...' : ''}</p>
        <p class="text-sm text-gray-500">收藏时间：${formatDate(collection.collected_at)}</p>
    `;
    
    // 添加点击事件
    collectionElement.addEventListener('click', () => {
        window.location.href = `6 article.html?id=${collection.article_id}`;
    });
    
    return collectionElement;
}

/**
 * 格式化日期
 */
function formatDate(dateString) {
    if (!dateString) return '未知时间';
    
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // 如果是今天
    if (diff < 24 * 60 * 60 * 1000 && date.getDate() === now.getDate()) {
        return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }
    
    // 如果是今年
    if (date.getFullYear() === now.getFullYear()) {
        return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
    }
    
    // 其他情况显示完整日期
    return date.toLocaleDateString('zh-CN');
}

// 将initPage函数暴露到全局作用域，以便HTML中的脚本可以调用
window.initPage = initPage;
globalThis.initPage = initPage;
/**
 * 个人信息编辑弹窗与提交
 */
function setupProfileEditor() {
    const btn = document.getElementById('edit-profile-btn');
    const modal = document.getElementById('editProfileModal');
    const cancelBtn = document.getElementById('ep-cancel');
    const form = document.getElementById('editProfileForm');
    if (!btn || !modal || !form) return;

    btn.addEventListener('click', async () => {
        try {
            const res = await apiRequest('/api/user/profile');
            const user = res.user_info || {};
            document.getElementById('ep-nickname').value = user.username || '';
            document.getElementById('ep-bio').value = user.bio || '';
            document.getElementById('ep-email').value = user.email || '';
            document.getElementById('ep-phone').value = user.phone || '';
            document.getElementById('ep-avatar').value = user.avatar || '';
            if (user.gender) {
                document.querySelectorAll('input[name="ep-gender"]').forEach(r => {
                    r.checked = (r.value === user.gender);
                });
            } else {
                document.querySelectorAll('input[name="ep-gender"]').forEach(r => r.checked = false);
            }
            if (user.birthday) {
                const d = String(user.birthday).slice(0, 10);
                const bd = document.getElementById('ep-birthday');
                if (bd) bd.value = d;
            }
        } catch (_) {}
        modal.style.display = 'flex';
    });

    cancelBtn && cancelBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            bio: document.getElementById('ep-bio').value.trim(),
            email: document.getElementById('ep-email').value.trim(),
            phone: document.getElementById('ep-phone').value.trim(),
            avatar: document.getElementById('ep-avatar').value.trim(),
            gender: (document.querySelector('input[name="ep-gender"]:checked')?.value || '').trim(),
            birthday: (document.getElementById('ep-birthday')?.value || '').trim()
        };
        // 移除空字段
        Object.keys(payload).forEach(k => { if (!payload[k]) delete payload[k]; });

        try {
            const result = await apiRequest('/api/user/profile/update', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            showNotification(result.message || '保存成功', 'success');
            modal.style.display = 'none';
            await loadUserData();
        } catch (err) {
            console.error('更新资料失败:', err);
            showNotification('保存失败，请稍后重试', 'error');
        }
    });
}

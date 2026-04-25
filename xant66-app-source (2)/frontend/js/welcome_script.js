import { initReloginButtons } from './auth.js';
import { debounce, showNotification } from './utils.js';

const state = {
    articles: [],
    displayArticles: [],
    searchTerm: '',
    sortBy: 'newest',
    visibleCount: 8
};

const PAGE_SIZE = 8;

function formatDate(value) {
    if (!value) return '发布时间未知';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

function getArticleDate(article) {
    return (
        article.created_at ||
        article.createdAt ||
        article.updated_at ||
        article.publish_time ||
        ''
    );
}

function getSnippet(article) {
    const raw = article.content || article.summary || article.body || '';
    const clean = String(raw).replace(/\s+/g, ' ').trim();
    if (!clean) return '点击查看完整内容，了解更多互助经验。';
    return clean.length > 80 ? `${clean.slice(0, 80)}...` : clean;
}

function createArticleNode(article) {
    const articleItem = document.createElement('div');
    articleItem.className = 'article-item';
    const category = article.category || '未分类';
    const dateText = formatDate(getArticleDate(article));
    const author = article.author || article.nickname || article.user_name || '匿名用户';

    articleItem.innerHTML = `
        <a href="6 article.html?id=${article.id}">${article.title || '未命名帖子'}</a>
        <div class="article-meta-row">
            <span class="article-pill">${category}</span>
            <span>作者：${author}</span>
            <span>${dateText}</span>
        </div>
        <p class="article-snippet">${getSnippet(article)}</p>
    `;
    return articleItem;
}

function updateResultCount() {
    const resultCount = document.getElementById('resultCount');
    if (!resultCount) return;
    const total = state.articles.length;
    const current = state.displayArticles.length;
    resultCount.textContent = `共 ${total} 篇，当前显示 ${current} 篇`;
}

function sortArticles(list) {
    return [...list].sort((a, b) => {
        if (state.sortBy === 'title') {
            return String(a.title || '').localeCompare(String(b.title || ''), 'zh-CN');
        }

        const aTime = new Date(getArticleDate(a)).getTime() || 0;
        const bTime = new Date(getArticleDate(b)).getTime() || 0;
        return state.sortBy === 'oldest' ? aTime - bTime : bTime - aTime;
    });
}

function renderArticles() {
    const articleList = document.querySelector('.article-list');
    if (!articleList) return;
    articleList.innerHTML = '';

    if (!state.displayArticles.length) {
        articleList.innerHTML = `
            <div class="no-results rich-empty">
                <i class="fa-regular fa-face-smile"></i>
                <h3>${state.searchTerm ? '没有找到匹配的帖子' : '暂时没有帖子'}</h3>
                <p>${state.searchTerm ? '换一个关键词试试，或按回车进行后端深度搜索。' : '发布第一篇互助经验，让更多人看到你的分享。'}</p>
                <a href="3 writing.html" class="btn">去发布帖子</a>
            </div>
        `;
        updateResultCount();
        return;
    }

    state.displayArticles.slice(0, state.visibleCount).forEach((article) => {
        articleList.appendChild(createArticleNode(article));
    });

    if (state.visibleCount < state.displayArticles.length) {
        const loadMore = document.createElement('button');
        loadMore.type = 'button';
        loadMore.className = 'btn load-more-btn';
        loadMore.textContent = `继续加载 ${Math.min(PAGE_SIZE, state.displayArticles.length - state.visibleCount)} 篇`;
        loadMore.addEventListener('click', () => {
            state.visibleCount += PAGE_SIZE;
            renderArticles();
        });
        articleList.appendChild(loadMore);
    }
    updateResultCount();
}

function applyFilters() {
    const keyword = state.searchTerm.toLowerCase();
    const filtered = state.articles.filter((article) => {
        if (!keyword) return true;
        const text = `${article.title || ''} ${article.content || ''} ${article.category || ''}`.toLowerCase();
        return text.includes(keyword);
    });

    state.displayArticles = sortArticles(filtered);
    state.visibleCount = PAGE_SIZE;
    renderArticles();
}

async function handleServerSearch() {
    if (!state.searchTerm) {
        applyFilters();
        return;
    }

    const articleList = document.querySelector('.article-list');
    if (articleList) {
        renderListSkeleton(articleList, '正在进行深度搜索...');
    }

    const token = sessionStorage.getItem('auth_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;

    try {
        const response = await fetch(`${window.location.origin}/api/articles/search`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ keyword: state.searchTerm })
        });
        const data = await response.json();
        if (response.ok && data.status === 'success') {
            state.displayArticles = sortArticles(data.results || []);
            renderArticles();
            showNotification(`搜索完成，找到 ${state.displayArticles.length} 篇相关帖子`, 'success');
            return;
        }
        showNotification(data.message || '搜索失败，已展示本地筛选结果', 'error');
    } catch (error) {
        console.error('搜索失败:', error);
        showNotification('搜索请求失败，已展示本地筛选结果', 'error');
    }

    applyFilters();
}

async function loadArticleList() {
    const articleList = document.querySelector('.article-list');
    if (!articleList) return;

    renderListSkeleton(articleList, '正在加载文章列表...');
    try {
        const response = await fetch(`${window.location.origin}/api/articles`);
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        if (data.status !== 'success') {
            throw new Error('接口返回状态异常');
        }
        state.articles = data.articles || [];
        applyFilters();
    } catch (error) {
        console.error('加载文章列表失败:', error);
        articleList.innerHTML = `
            <div class="no-results rich-empty">
                <i class="fa-solid fa-wifi"></i>
                <h3>文章列表加载失败</h3>
                <p>请检查网络或后端服务状态，然后刷新页面重试。</p>
            </div>
        `;
        showNotification('文章列表加载失败，请检查网络后重试', 'error');
    }
}

function renderListSkeleton(container, message) {
    container.innerHTML = `
        <div class="forum-skeleton" aria-label="${message}">
            <div class="loading">${message}</div>
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
        </div>
    `;
}

window.addEventListener('DOMContentLoaded', () => {
    initReloginButtons();

    const searchInput = document.getElementById('searchInput');
    const sortSelect = document.getElementById('sortSelect');
    const clearSearchBtn = document.getElementById('clearSearchBtn');

    if (searchInput) {
        const onTyping = debounce((event) => {
            state.searchTerm = event.target.value.trim();
            applyFilters();
        }, 200);
        searchInput.addEventListener('input', onTyping);
        searchInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                state.searchTerm = event.target.value.trim();
                handleServerSearch();
            }
        });
    }

    if (sortSelect) {
        sortSelect.addEventListener('change', (event) => {
            state.sortBy = event.target.value;
            applyFilters();
        });
    }

    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', () => {
            state.searchTerm = '';
            if (searchInput) searchInput.value = '';
            applyFilters();
            showNotification('已清空搜索条件');
        });
    }

    loadArticleList();
});

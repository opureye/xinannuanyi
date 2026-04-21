import { showNotification } from './utils.js';

function normalizePath(pathname) {
    const value = pathname.split('/').pop() || '';
    try {
        return decodeURIComponent(value).toLowerCase();
    } catch (error) {
        return value.toLowerCase();
    }
}

function initActiveNav() {
    const currentFile = normalizePath(window.location.pathname);
    const navLinks = document.querySelectorAll('.navbar .nav-btn[href]');
    if (!navLinks.length) return;

    navLinks.forEach((link) => {
        const href = link.getAttribute('href') || '';
        const linkFile = normalizePath(href);
        if (linkFile && currentFile && linkFile === currentFile) {
            link.classList.add('active');
            link.setAttribute('aria-current', 'page');
        }
    });
}

function initFixedNavSpacing() {
    const topNav = document.querySelector('body > .navbar');
    if (!topNav) return;
    document.body.classList.add('has-fixed-nav');

    const applyOffset = () => {
        const offset = Math.ceil(topNav.offsetHeight + 28);
        document.body.style.setProperty('--nav-offset', `${offset}px`);
    };

    window.addEventListener('resize', applyOffset);
    applyOffset();
}

function initSessionEntry() {
    const currentFile = normalizePath(window.location.pathname);
    const isAuthPage = currentFile === '4 login.html' || currentFile === '8 register.html';
    if (isAuthPage) return;

    const reloginInNav = Array.from(document.querySelectorAll('.navbar .nav-btn')).find((btn) => {
        const href = normalizePath(btn.getAttribute('href') || '');
        return href === '4 login.html' || btn.textContent.includes('重新登录');
    });

    if (reloginInNav) {
        reloginInNav.remove();
    }

    const sessionEntry = document.createElement('button');
    sessionEntry.type = 'button';
    sessionEntry.className = 'session-entry';
    const hasToken = !!sessionStorage.getItem('auth_token');
    sessionEntry.textContent = hasToken ? '退出登录' : '去登录';

    sessionEntry.addEventListener('click', () => {
        if (hasToken) {
            sessionStorage.removeItem('auth_token');
            sessionStorage.removeItem('user_role');
            sessionStorage.removeItem('username');
            localStorage.removeItem('loggedInUser');
            showNotification('已退出登录');
        }
        window.location.href = '4 login.html';
    });
    document.body.appendChild(sessionEntry);
}

function initBackToTop() {
    const backToTop = document.createElement('button');
    backToTop.type = 'button';
    backToTop.className = 'back-to-top';
    backToTop.setAttribute('aria-label', '回到顶部');
    backToTop.textContent = '↑';
    document.body.appendChild(backToTop);

    const toggleVisibility = () => {
        const shouldShow = window.scrollY > 240;
        backToTop.classList.toggle('show', shouldShow);
    };

    window.addEventListener('scroll', toggleVisibility, { passive: true });
    backToTop.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    toggleVisibility();
}

function initSearchShortcut() {
    window.addEventListener('keydown', (event) => {
        if (event.key !== '/' || event.ctrlKey || event.altKey || event.metaKey) {
            return;
        }
        const activeElement = document.activeElement;
        const isTyping =
            activeElement &&
            (activeElement.tagName === 'INPUT' ||
                activeElement.tagName === 'TEXTAREA' ||
                activeElement.isContentEditable);
        if (isTyping) return;

        const searchInput = document.getElementById('searchInput');
        if (!searchInput) return;

        event.preventDefault();
        searchInput.focus();
        showNotification('已聚焦搜索框，直接输入即可');
    });
}

function initNetworkHint() {
    window.addEventListener('offline', () => {
        showNotification('网络已断开，部分功能可能不可用', 'error');
    });
    window.addEventListener('online', () => {
        showNotification('网络已恢复');
    });
}

window.addEventListener('DOMContentLoaded', () => {
    initFixedNavSpacing();
    initSessionEntry();
    initActiveNav();
    initBackToTop();
    initSearchShortcut();
    initNetworkHint();
});

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

function initScrollProgress() {
    const progress = document.createElement('div');
    progress.className = 'scroll-progress';
    document.body.appendChild(progress);

    const updateProgress = () => {
        const scrollable = document.documentElement.scrollHeight - window.innerHeight;
        const ratio = scrollable > 0 ? window.scrollY / scrollable : 0;
        progress.style.width = `${Math.min(100, Math.max(0, ratio * 100))}%`;
    };

    window.addEventListener('scroll', updateProgress, { passive: true });
    window.addEventListener('resize', updateProgress);
    updateProgress();
}

function initFixedNavSpacing() {
    const topNav = document.querySelector('body > .navbar');
    if (!topNav) return;
    document.body.classList.add('has-fixed-nav');

    const applyOffset = () => {
        const offset = Math.ceil(topNav.offsetHeight + 24);
        document.body.style.setProperty('--nav-offset', `${offset}px`);
    };

    window.addEventListener('resize', applyOffset);
    applyOffset();
}

function initSessionEntry() {
    const legacyFloatingSelector = '.session-entry, .quick-dock, .back-to-top, button.fixed.bottom-8.right-8, button.fixed.bottom-6.right-6';
    const removeLegacySessionEntry = () => {
        document.querySelectorAll(legacyFloatingSelector).forEach((entry) => entry.remove());
    };
    removeLegacySessionEntry();
    const observer = new MutationObserver(removeLegacySessionEntry);
    observer.observe(document.body, { childList: true, subtree: true });

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
}

function getQuickActions() {
    return [
        { href: '1 me.html', label: '首页', icon: '🏠' },
        { href: '5 welcome.html', label: '论坛', icon: '💬' },
        { href: '3 writing.html', label: '发帖', icon: '✍️' },
        { href: '13 myspace.html', label: '我的', icon: '👤' }
    ];
}

function initCommandPalette() {
    const modal = document.createElement('div');
    modal.className = 'experience-modal';
    modal.innerHTML = `
        <div class="command-panel" role="dialog" aria-modal="true" aria-label="快捷菜单">
            <header>
                <strong>快捷菜单</strong>
                <span>按 Esc 关闭，快速进入常用模块</span>
            </header>
            <div class="command-list">
                ${getQuickActions().map((action) => `<a href="${action.href}">${action.icon} ${action.label}</a>`).join('')}
                <button type="button" data-action="logout">🔑 退出登录 / 重新登录</button>
            </div>
        </div>
    `;
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.classList.remove('show');
        }
        const action = event.target?.getAttribute?.('data-action');
        if (action === 'logout') {
            sessionStorage.removeItem('auth_token');
            sessionStorage.removeItem('user_role');
            sessionStorage.removeItem('username');
            localStorage.removeItem('loggedInUser');
            window.location.href = '4 login.html';
        }
    });
    document.body.appendChild(modal);

    window.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            modal.classList.remove('show');
            return;
        }
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
            event.preventDefault();
            modal.classList.toggle('show');
        }
    });
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
    initScrollProgress();
    initCommandPalette();
    initSearchShortcut();
    initNetworkHint();
});

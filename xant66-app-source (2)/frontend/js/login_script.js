import { showNotification } from './utils.js';

const API_BASE_URL = window.location.origin;
const API_TIMEOUT = 30000;

function setSubmitting(button, isSubmitting) {
    if (!button) return;
    button.disabled = isSubmitting;
    button.textContent = isSubmitting ? '登录中...' : '立即登录';
}

async function login(username, password) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
    try {
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
            signal: controller.signal
        });

        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload?.message || `请求失败: ${response.status}`);
        }
        return payload;
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error('登录请求超时，请检查网络连接');
        }
        throw error;
    } finally {
        clearTimeout(timeoutId);
    }
}

function redirectByRole(role) {
    if (role === '管理员') {
        window.location.href = '9 audit_home.html';
        return;
    }
    window.location.href = '1 me.html';
}

window.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const loginButton = document.getElementById('loginButton');

    if (!loginForm || !usernameInput || !passwordInput || !loginButton) return;

    const token = sessionStorage.getItem('auth_token');
    const role = sessionStorage.getItem('user_role');
    if (token && role) {
        redirectByRole(role);
        return;
    }

    const cachedUsername = localStorage.getItem('last_login_username');
    if (cachedUsername && !usernameInput.value) {
        usernameInput.value = cachedUsername;
        showNotification(`欢迎回来，${cachedUsername}`);
        passwordInput.focus();
    }

    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();
        if (!username || !password) {
            showNotification('请输入用户名和密码', 'error');
            return;
        }

        setSubmitting(loginButton, true);
        try {
            const result = await login(username, password);
            if (!result.success) {
                showNotification(result.message || '登录失败，请检查账号信息', 'error');
                return;
            }

            sessionStorage.setItem('auth_token', result.access_token);
            sessionStorage.setItem('user_role', result.role);
            sessionStorage.setItem('username', username);
            localStorage.setItem('last_login_username', username);
            localStorage.setItem(
                'loggedInUser',
                JSON.stringify({
                    username,
                    role: result.role,
                    access_token: result.access_token
                })
            );

            showNotification('登录成功，正在跳转...', 'success');
            setTimeout(() => redirectByRole(result.role), 450);
        } catch (error) {
            console.error('登录请求失败:', error);
            showNotification(error.message || '登录请求失败，请稍后重试', 'error');
        } finally {
            setSubmitting(loginButton, false);
        }
    });
});

/**
 * 认证状态管理模块
 */
import { validateToken } from './api.js';

// 检查用户是否已登录
export function isLoggedIn() {
    const token = sessionStorage.getItem('auth_token'); // 修改为sessionStorage
    return !!token;
}

// 获取当前用户角色
export function getUserRole() {
    return sessionStorage.getItem('user_role') || '使用者'; // 修改为sessionStorage
}

// 执行登出操作
export function logout() {
    sessionStorage.removeItem('auth_token'); // 修改为sessionStorage
    sessionStorage.removeItem('user_role'); // 修改为sessionStorage
    sessionStorage.removeItem('username'); // 清除用户名
    localStorage.removeItem('loggedInUser'); // 清除localStorage中的用户信息
    window.location.href = '4 login.html';
}

// 验证用户认证状态
export async function checkAuthStatus() {
    if (isLoggedIn()) {
        // 验证令牌是否有效
        const isValid = await validateToken();
        if (!isValid) {
            logout();
            return false;
        }
        return true;
    }
    return false;
}

// 保护需要认证的页面
export async function protectPage(requiredRole = null) {
    const isAuthenticated = await checkAuthStatus();
    
    if (!isAuthenticated) {
        window.location.href = '4 login.html';
        return false;
    }
    
    // 如果需要特定角色
    if (requiredRole && getUserRole() !== requiredRole) {
        window.location.href = '1 me.html'; // 重定向到普通用户页面
        return false;
    }
    
    return true;
}

/**
 * 初始化所有"重新登录"按钮的点击事件处理器
 */
export function initReloginButtons() {
    // 查找所有包含"重新登录"文本的导航按钮
    const reloginButtons = document.querySelectorAll('a.nav-btn');
    
    reloginButtons.forEach(button => {
        if (button.textContent.includes('重新登录')) {
            button.addEventListener('click', function(e) {
                e.preventDefault(); // 阻止默认链接行为
                console.log('执行重新登录操作');
                logout(); // 调用登出函数清除认证信息并跳转到登录页
            });
        }
    });
}
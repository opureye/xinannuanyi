/**
 * 登录表单提交处理 - 独立版本
 */
(function() {
    // API基础配置
    const API_BASE_URL = window.location.origin;
    const API_TIMEOUT = 30000;
    
    // 内部实现的通知函数
    function showNotification(message, type = 'info') {
        // 创建简单的通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // 设置样式
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.padding = '12px 20px';
        notification.style.borderRadius = '4px';
        notification.style.color = 'white';
        notification.style.fontSize = '14px';
        notification.style.zIndex = '9999';
        notification.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
        notification.style.transition = 'all 0.3s ease';
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-10px)';
        
        // 根据类型设置背景色
        if (type === 'error') {
            notification.style.backgroundColor = '#e74c3c';
        } else if (type === 'success') {
            notification.style.backgroundColor = '#2ecc71';
        } else {
            notification.style.backgroundColor = '#3498db';
        }
        
        // 添加到页面
        document.body.appendChild(notification);
        
        // 显示动画
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        }, 10);
        
        // 3秒后移除
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
    
    // 内部实现的登录函数
    async function login(username, password) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
            
            const response = await fetch(`${API_BASE_URL}/api/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`请求失败: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('登录请求错误:', error);
            if (error.name === 'AbortError') {
                throw new Error('登录请求超时，请检查网络连接');
            }
            throw error;
        }
    }
    
    // 等待DOM内容加载完成
    window.addEventListener('DOMContentLoaded', function() {
        console.log('DOM内容加载完成，初始化登录表单');
        
        const loginForm = document.getElementById('loginForm');
        
        if (loginForm) {
            // 定义必要的变量
            const usernameInput = document.getElementById('username');
            const passwordInput = document.getElementById('password');
            const loginButton = document.getElementById('loginButton');
            
            console.log('登录表单元素获取完成:', {
                loginForm: !!loginForm,
                usernameInput: !!usernameInput,
                passwordInput: !!passwordInput,
                loginButton: !!loginButton
            });
            
            // 检查是否已有令牌，如果有则跳转到相应页面
            const token = sessionStorage.getItem('auth_token');
            const role = sessionStorage.getItem('user_role');
            
            if (token && role) {
                // 已登录，跳转到对应角色的首页
                if (role === '管理员') {
                    window.location.href = '9 audit_home.html';
                } else {
                    window.location.href = '1 me.html';
                }
                return;
            }
            
            // 为登录按钮添加事件监听
            loginButton.addEventListener('click', async function() {
                const username = usernameInput.value.trim();
                const password = passwordInput.value.trim();
                
                // 简单的表单验证
                if (!username || !password) {
                    showNotification('请输入用户名和密码', 'error');
                    return;
                }
                
                try {
                    // 禁用登录按钮，防止重复提交
                    loginButton.disabled = true;
                    loginButton.textContent = '登录中...';
                    
                    // 调用登录API
                    const result = await login(username, password);
                    
                    if (result.success) {
                        // 登录成功，保存令牌和角色信息
                        sessionStorage.setItem('auth_token', result.access_token);
                        sessionStorage.setItem('user_role', result.role);
                        sessionStorage.setItem('username', username);
                        
                        // 保存完整的用户信息到localStorage，供getLoggedInUser()使用
                        const userInfo = {
                            username: username,
                            role: result.role,
                            access_token: result.access_token
                        };
                        localStorage.setItem('loggedInUser', JSON.stringify(userInfo));
                        
                        // 根据角色跳转到不同页面
                        if (result.role === '管理员') {
                            window.location.href = '9 audit_home.html';
                        } else {
                            window.location.href = '1 me.html';
                        }
                    } else {
                        // 登录失败，显示错误信息
                        // 特别处理账号被封禁的情况
                        if (result.message && result.message.includes('你的账号因为违规被封禁')) {
                            showNotification(result.message, 'error');
                        } else {
                            showNotification('登录失败: ' + result.message, 'error');
                        }
                    }
                } catch (error) {
                    console.error('登录请求失败:', error);
                    showNotification('登录请求失败，请稍后重试', 'error');
                } finally {
                    // 恢复登录按钮状态
                    loginButton.disabled = false;
                    loginButton.textContent = '登录';
                }
            });
            
            // 为密码输入框添加回车事件
            passwordInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    loginButton.click();
                }
            });
        }
    });
})();

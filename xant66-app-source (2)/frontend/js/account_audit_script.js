// 导入共享的SDK工具模块 - 使用正确的函数名initAIModule
import { initAIModule } from './sdk_utils.js';

// 在文件顶部初始化AI模块
initAIModule();

// 获取所有用户
// 修改fetchAllUsers函数，添加日志和错误处理
// 1. 修改fetchAllUsers函数的认证头
// 增强fetchAllUsers函数，添加数据预处理
async function fetchAllUsers() {
  try {
    const token = sessionStorage.getItem('auth_token');
    console.log('使用的认证令牌:', token);
    
    if (!token) {
      showNotification('未找到认证令牌，请重新登录', 'error');
      window.location.href = '4 login.html';
      return;
    }

    const response = await fetch('/api/admin/users', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`  // 添加Bearer前缀
      }
    });
    
    // 添加详细的错误处理
    if (!response.ok) {
      if (response.status === 401) {
        console.error('认证失败，清除无效令牌');
        sessionStorage.removeItem('auth_token');
        sessionStorage.removeItem('user_role');
        showNotification('认证失败，请重新登录', 'error');
        window.location.href = '4 login.html';
      } else if (response.status === 403) {
        showNotification('权限不足，您不是管理员', 'error');
      } else if (response.status === 409) {
        showNotification('系统繁忙，请稍后再试', 'error');
      } else {
        throw new Error('获取用户列表失败，HTTP状态码: ' + response.status);
      }
      return;
    }

    const data = await response.json();
    console.log('用户列表数据:', data);
    
    if (data.success && data.users) {
      // 添加数据预处理，确保数据一致性
      const processedUsers = data.users.map(user => ({
        ...user,
        // 确保is_banned字段存在
        is_banned: typeof user.is_banned === 'boolean' ? user.is_banned : false,
        // 如果需要，可以根据is_banned反推status字段
        status: user.is_banned ? 'banned' : 'active'
      }));
      renderUserList(processedUsers);
    } else {
      showNotification('获取用户列表失败: ' + (data.message || '未知错误'), 'error');
    }
  } catch (error) {
    console.error('获取用户列表时发生错误:', error);
    showNotification('获取用户列表时发生错误: ' + error.message, 'error');
  }
}

// 搜索用户
// 同时修改searchUsers函数的认证头格式
// 2. 修改searchUsers函数的认证头
async function searchUsers(keyword) {
  try {
    const response = await fetch('/api/admin/users/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${sessionStorage.getItem('auth_token')}`  // 添加Bearer前缀
      },
      body: JSON.stringify({ keyword })
    });
    
    if (!response.ok) {
      if (response.status === 409) {
        showNotification('系统繁忙，请稍后再试', 'error');
        return;
      }
      throw new Error('搜索用户失败');
    }
    
    const data = await response.json();
    if (data.success) {
      // 添加数据预处理
      const processedUsers = data.users.map(user => ({
        ...user,
        is_banned: typeof user.is_banned === 'boolean' ? user.is_banned : false,
        status: user.is_banned ? 'banned' : 'active'
      }));
      renderUserList(processedUsers);
    } else {
      showNotification('搜索用户失败: ' + data.message, 'error');
    }
  } catch (error) {
    console.error('搜索用户时发生错误:', error);
    showNotification('搜索用户时发生错误: ' + error.message, 'error');
  }
}

// 渲染用户列表
function renderUserList(users) {
  const tableBody = document.querySelector('#user-table tbody');
  tableBody.innerHTML = '';
  
  if (users.length === 0) {
    tableBody.innerHTML = '<tr><td colspan="8" class="text-center py-4">没有找到用户</td></tr>';
    return;
  }
  
  users.forEach(user => {
    // 检查用户是否被停用
    const isDeactivated = user.bio && user.bio.includes('此用户已被停用');
    
    // 修复：使用后端实际返回的is_banned字段
    const isBanned = user.is_banned || false; // 添加默认值确保安全
    
    // 设置状态类和文本
    let statusClass = 'text-green-500';
    let statusText = '正常';
    
    if (isBanned) {
      statusClass = 'text-red-500';
      statusText = '已封禁';
    } else if (isDeactivated) {
      statusClass = 'text-gray-500';
      statusText = '已停用';
    }
    
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${user.username}</td>
      <td>${user.phone}</td>
      <td>${user.email}</td>
      <td>${user.role}</td>
      <td>${new Date(user.created_at).toLocaleString()}</td>
      <td class="${statusClass}">${statusText}</td>
      <td>
        ${!isDeactivated && user.role !== '管理员' ? 
          `
          ${!isBanned ? 
            `<button class="ban-btn bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1 rounded mr-2" data-username="${user.username}">封禁</button>` : 
            `<button class="unban-btn bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded mr-2" data-username="${user.username}">解封</button>`
          }
          <button class="delete-btn bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded" data-username="${user.username}">删除</button>
          ` : 
          '<span class="text-gray-400">无操作</span>'
        }
      </td>
    `;
    tableBody.appendChild(row);
  });
  
  // 为封禁按钮添加事件监听
  document.querySelectorAll('.ban-btn').forEach(button => {
    button.addEventListener('click', function() {
      const username = this.getAttribute('data-username');
      if (confirm(`确定要封禁用户 ${username} 吗？封禁后用户将无法登录！`)) {
        banUser(username);
      }
    });
  });
  
  // 为解封按钮添加事件监听
  document.querySelectorAll('.unban-btn').forEach(button => {
    button.addEventListener('click', function() {
      const username = this.getAttribute('data-username');
      if (confirm(`确定要解封用户 ${username} 吗？解封后用户可以重新登录！`)) {
        unbanUser(username);
      }
    });
  });
  
  // 为删除按钮添加事件监听
  document.querySelectorAll('.delete-btn').forEach(button => {
    button.addEventListener('click', function() {
      const username = this.getAttribute('data-username');
      if (confirm(`确定要永久删除用户 ${username} 吗？此操作不可撤销，将删除用户的所有数据！`)) {
        deleteUser(username);
      }
    });
  });
}

// 封禁用户
async function banUser(username) {
  try {
    const response = await fetch('/api/admin/user/ban', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${sessionStorage.getItem('auth_token')}`  // 添加Bearer前缀
      },
      body: JSON.stringify({ username })
    });
    
    if (!response.ok) {
      if (response.status === 409) {
        showNotification('系统繁忙，请稍后再试', 'error');
        return;
      }
      throw new Error('封禁用户失败');
    }
    
    const data = await response.json();
    if (data.success) {
      showNotification(`成功封禁用户 ${username}`, 'success');
      // 重新加载用户列表
      fetchAllUsers();
    } else {
      showNotification('封禁用户失败: ' + data.message, 'error');
    }
  } catch (error) {
    console.error('封禁用户时发生错误:', error);
    showNotification('封禁用户时发生错误: ' + error.message, 'error');
  }
}

// 解封用户
async function unbanUser(username) {
  try {
    const response = await fetch('/api/admin/user/unban', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${sessionStorage.getItem('auth_token')}`  // 添加Bearer前缀
      },
      body: JSON.stringify({ username })
    });
    
    if (!response.ok) {
      if (response.status === 409) {
        showNotification('系统繁忙，请稍后再试', 'error');
        return;
      }
      throw new Error('解封用户失败');
    }
    
    const data = await response.json();
    if (data.success) {
      showNotification(`成功解封用户 ${username}`, 'success');
      // 重新加载用户列表
      fetchAllUsers();
    } else {
      showNotification('解封用户失败: ' + data.message, 'error');
    }
  } catch (error) {
    console.error('解封用户时发生错误:', error);
    showNotification('解封用户时发生错误: ' + error.message, 'error');
  }
}

// 删除用户
// 5. 修改deleteUser函数的认证头
async function deleteUser(username) {
  try {
    const response = await fetch(`/api/admin/user/delete?username=${encodeURIComponent(username)}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${sessionStorage.getItem('auth_token')}`  // 添加Bearer前缀
      }
    });
    
    if (!response.ok) {
      if (response.status === 409) {
        showNotification('系统繁忙，请稍后再试', 'error');
        return;
      }
      throw new Error('删除用户失败');
    }
    
    const data = await response.json();
    if (data.success) {
      showNotification(`成功删除用户 ${username}`, 'success');
      // 重新加载用户列表
      fetchAllUsers();
    } else {
      showNotification('删除用户失败: ' + data.message, 'error');
    }
  } catch (error) {
    console.error('删除用户时发生错误:', error);
    showNotification('删除用户时发生错误: ' + error.message, 'error');
  }
}

// 显示通知
function showNotification(message, type = 'info') {
  // 创建通知元素
  const notification = document.createElement('div');
  notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 max-w-xs transform transition-all duration-300 translate-x-full`;
  
  // 设置通知样式
  if (type === 'success') {
    notification.classList.add('bg-green-500', 'text-white');
  } else if (type === 'error') {
    notification.classList.add('bg-red-500', 'text-white');
  } else {
    notification.classList.add('bg-blue-500', 'text-white');
  }
  
  notification.textContent = message;
  document.body.appendChild(notification);
  
  // 显示通知
  setTimeout(() => {
    notification.classList.remove('translate-x-full');
  }, 10);
  
  // 3秒后隐藏通知
  setTimeout(() => {
    notification.classList.add('translate-x-full');
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 300);
  }, 3000);
}

// 1. 修改DOMContentLoaded事件处理，统一从sessionStorage获取token
document.addEventListener('DOMContentLoaded', function() {
    // 检查用户是否已登录且为管理员
    const token = sessionStorage.getItem('auth_token');
    if (!token) {
        showNotification('请先登录', 'error');
        setTimeout(() => {
            window.location.href = '4 login.html';
        }, 1500);
        return;
    }
    
    // 初始化用户列表
    fetchAllUsers();
    
    // 搜索按钮事件监听
    const searchButton = document.getElementById('search-button');
    const searchInput = document.getElementById('search-input');
    
    searchButton.addEventListener('click', function() {
        const keyword = searchInput.value.trim();
        if (keyword) {
            searchUsers(keyword);
        } else {
            fetchAllUsers(); // 如果搜索框为空，显示所有用户
        }
    });
    
    // 按回车键执行搜索
    searchInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            searchButton.click();
        }
    });
});

// 2. 修改checkAdminPermission函数，统一从sessionStorage获取role
async function checkAdminPermission() {
  try {
    const userRole = sessionStorage.getItem('user_role');
    if (!userRole || userRole !== '管理员') {
      showNotification('您没有管理员权限，无法执行此操作', 'error');
      // 3秒后重定向到首页
      setTimeout(() => {
        window.location.href = '1 me.html';
      }, 3000);
    }
  } catch (error) {
    console.error('检查权限时发生错误:', error);
    showNotification('检查权限时发生错误', 'error');
  }
}
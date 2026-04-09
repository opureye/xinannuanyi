// 显示通知消息
export function showNotification(message, type = 'info') {
    // 检查是否已有通知元素
    let notification = document.querySelector('.notification');
    
    if (!notification) {
        // 创建通知元素
        notification = document.createElement('div');
        notification.className = 'notification';
        document.body.appendChild(notification);
    }
    
    // 设置通知内容并显示
    notification.textContent = message;
    notification.classList.add('show');
    
    // 根据类型添加样式
    notification.className = `notification ${type}`;
    
    // 3秒后隐藏通知
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// 显示错误消息
export function showError(message) {
    showNotification(message, 'error');
}

// 获取URL参数
export function getUrlParam(paramName) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(paramName);
}

// 检查对象是否为空
export function isEmpty(obj) {
    return obj === null || obj === undefined || Object.keys(obj).length === 0;
}

// 防抖函数
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 为了向后兼容，保留默认导出
export default {
    showNotification,
    showError,
    getUrlParam,
    isEmpty,
    debounce
};
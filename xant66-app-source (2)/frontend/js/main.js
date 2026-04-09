// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    // DOM元素引用
    const themeToggle = document.getElementById('theme-toggle');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const settingsBtn = document.getElementById('settings-btn');
    const settingsPanel = document.getElementById('settings-panel');
    const closeSettings = document.getElementById('close-settings');
    const newChatBtn = document.getElementById('new-chat-btn');
    const overlay = document.createElement('div');
    
    // 创建遮罩层（用于移动设备）
    overlay.className = 'overlay';
    document.body.appendChild(overlay);
    
    // 检查本地存储中的主题设置
    if (localStorage.getItem('darkMode') === 'true') {
        document.documentElement.classList.add('dark-mode');
        themeToggle.innerHTML = '<i class="fa fa-sun-o text-neutral-700"></i>';
    }
    
    // 主题切换功能
    themeToggle.addEventListener('click', function() {
        const isDarkMode = document.documentElement.classList.toggle('dark-mode');
        localStorage.setItem('darkMode', isDarkMode);
        
        // 更新图标
        if (isDarkMode) {
            themeToggle.innerHTML = '<i class="fa fa-sun-o text-neutral-700"></i>';
        } else {
            themeToggle.innerHTML = '<i class="fa fa-moon-o text-neutral-700"></i>';
        }
    });
    
    // 侧边栏控制（移动设备）
    function toggleSidebar() {
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    }
    
    sidebarToggle.addEventListener('click', toggleSidebar);
    overlay.addEventListener('click', toggleSidebar);
    
    // 设置面板控制
    function openSettings() {
        settingsPanel.style.display = 'flex';
        setTimeout(() => {
            settingsPanel.classList.add('active');
        }, 10);
    }
    
    function closeSettingsPanel() {
        settingsPanel.classList.remove('active');
        setTimeout(() => {
            settingsPanel.style.display = 'none';
        }, 300);
    }
    
    settingsBtn.addEventListener('click', openSettings);
    closeSettings.addEventListener('click', closeSettingsPanel);
    
    // 点击设置面板外部关闭
    settingsPanel.addEventListener('click', function(e) {
        if (e.target === settingsPanel) {
            closeSettingsPanel();
        }
    });
    
    // 新对话按钮
    newChatBtn.addEventListener('click', function() {
        // 清空当前对话
        const chatContainer = document.getElementById('chat-container');
        chatContainer.innerHTML = `
            <div class="flex justify-center py-8">
                <div class="text-center max-w-md">
                    <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 text-primary mb-4">
                        <i class="fa fa-robot text-3xl"></i>
                    </div>
                    <h2 class="text-2xl font-bold text-neutral-800 mb-2">新的对话已开始</h2>
                    <p class="text-neutral-600">请输入你的问题，我会尽力为你解答。</p>
                </div>
            </div>
        `;
        
        // 在移动设备上关闭侧边栏
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
        }
        
        // 聚焦到输入框
        document.getElementById('message-input').focus();
    });
    
    // 对话历史项点击事件
    const chatHistoryItems = document.querySelectorAll('#chat-history button');
    chatHistoryItems.forEach(item => {
        item.addEventListener('click', function() {
            // 移除其他项的激活状态
            chatHistoryItems.forEach(i => i.classList.remove('bg-primary/10', 'text-neutral-800'));
            chatHistoryItems.forEach(i => i.classList.add('bg-neutral-100', 'text-neutral-700'));
            
            // 添加当前项的激活状态
            this.classList.remove('bg-neutral-100', 'text-neutral-700');
            this.classList.add('bg-primary/10', 'text-neutral-800');
            
            // 在移动设备上关闭侧边栏
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('active');
                overlay.classList.remove('active');
            }
            
            // 这里可以添加加载对应对话历史的逻辑
            const chatTitle = this.querySelector('span').textContent;
            showNotification(`加载对话: ${chatTitle}`);
        });
    });
    
    // 通知提示功能
    function showNotification(message) {
        // 检查是否已有通知元素
        let notification = document.querySelector('.notification');
        
        if (!notification) {
            // 创建通知元素
            notification = document.createElement('div');
            notification.className = 'notification fixed bottom-4 right-4 bg-neutral-800 text-white px-4 py-2 rounded-lg shadow-lg z-50 transform translate-y-20 opacity-0 transition-all duration-300';
            document.body.appendChild(notification);
        }
        
        // 设置通知内容并显示
        notification.textContent = message;
        setTimeout(() => {
            notification.classList.remove('translate-y-20', 'opacity-0');
        }, 10);
        
        // 3秒后隐藏通知
        setTimeout(() => {
            notification.classList.add('translate-y-20', 'opacity-0');
        }, 3000);
    }
    
    // 初始化页面
    function init() {
        // 确保设置面板初始隐藏
        settingsPanel.style.display = 'none';
        
        // 聚焦到输入框
        document.getElementById('message-input').focus();
        
        // 检查屏幕宽度，在移动设备上初始化侧边栏状态
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('active');
        } else {
            sidebar.classList.add('active');
        }
    }
    
    // 窗口大小变化时调整布局
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            sidebar.classList.add('active');
            overlay.classList.remove('active');
        } else {
            sidebar.classList.remove('active');
        }
    });
    
    // 初始化
    init();
});

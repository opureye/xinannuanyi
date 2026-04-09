/**
 * AI助手侧边栏模块
 */
// 导入声明必须放在模块顶层
import { getAIResponse } from './api.js';
import { showNotification } from './utils.js';
import { initAIModule, getAIAccessToken } from './sdk_utils.js';

// 定义全局变量作为导出目标
let aiSidebarInstance = null;

// 为了处理可能的模块加载错误，创建安全的模块加载检查
function safeImport() {
    try {
        // 确认所有必要的导入模块可用
        const requiredModules = {
            getAIResponse: typeof getAIResponse === 'function',
            showNotification: typeof showNotification === 'function',
            initAIModule: typeof initAIModule === 'function',
            getAIAccessToken: typeof getAIAccessToken === 'function'
        };
        
        console.log('AI侧边栏模块依赖检查:', requiredModules);
        return requiredModules;
    } catch (error) {
        console.error('AI侧边栏模块依赖检查失败:', error);
        return { allFailed: true };
    }
}

// 安全检查导入的模块
const modules = safeImport();
if (modules.allFailed) {
    console.error('❌ AI侧边栏核心模块缺失，无法初始化');
    window.aiSidebarError = new Error('核心模块缺失');
}

// 定义AISidebar类
class AISidebar {
    constructor() {
        // 初始化标志
        this.isInitialized = false;
        this.isProcessing = false;
        this.messages = [];
        this.elements = {
            toggle: null,
            panel: null,
            close: null,
            form: null,
            input: null,
            chatContainer: null,
            sendBtn: null,
            clearBtn: null // 添加清除按钮引用
        };
        console.log('AISidebar实例已创建');
    }

    /**
     * 初始化AI侧边栏
     */
    init() {
        console.log('开始初始化AI侧边栏...');
        if (this.isInitialized) {
            console.log('AI侧边栏已经初始化，跳过重复初始化');
            return;
        }

        try {
            // 初始化AI模块
            console.log('初始化AI模块...');
            const aiInitResult = initAIModule();
            console.log('AI模块初始化结果:', aiInitResult);

            // 检查API密钥是否配置
            const apiKey = getAIAccessToken();
            if (!apiKey) {
                console.warn('⚠️ 未配置DeepSeek API密钥，AI功能可能受限');
            }

            // 创建侧边栏DOM元素
            console.log('创建侧边栏DOM元素...');
            this.createSidebarElements();
            console.log('侧边栏DOM元素创建完成');

            // 检查DOM元素是否正确获取
            console.log('侧边栏元素检查:', {
                toggle: !!this.elements.toggle,
                panel: !!this.elements.panel,
                close: !!this.elements.close
            });

            // 如果关键元素缺失，尝试修复
            if (!this.elements.toggle || !this.elements.panel) {
                console.error('❌ 关键DOM元素缺失，尝试重新创建...');
                this.createSidebarElements();
                // 再次检查
                if (!this.elements.toggle || !this.elements.panel) {
                    throw new Error('无法创建关键DOM元素');
                }
            }

            // 绑定事件
            console.log('绑定事件...');
            this.bindEvents();
            console.log('事件绑定完成');

            // 初始化完成
            this.isInitialized = true;
            console.log('✅ AI助手侧边栏初始化完成！');
        } catch (error) {
            console.error('❌ AI侧边栏初始化失败:', error);
            // 如果有showNotification函数可用，则显示错误通知
            if (typeof showNotification === 'function') {
                showNotification('AI侧边栏初始化失败: ' + error.message, 'error');
            }
        }
    }

    /**
     * 创建侧边栏DOM元素
     */
    createSidebarElements() {
        // 先检查是否已经存在侧边栏元素
        let existingSidebar = document.querySelector('.ai-sidebar');
        if (existingSidebar) {
            console.log('侧边栏元素已存在，移除旧元素重新创建');
            existingSidebar.remove();
        }

        // 创建侧边栏容器
        const sidebar = document.createElement('div');
        sidebar.className = 'ai-sidebar';
        sidebar.innerHTML = `
            <div class="ai-sidebar-toggle" id="ai-sidebar-toggle">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
            </div>
            <div class="ai-sidebar-panel" id="ai-sidebar-panel">
                <div class="ai-sidebar-header">
                    <div class="ai-header-content">
                        <div class="ai-avatar">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="10"></circle>
                                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                                <line x1="12" y1="17" x2="12.01" y2="17"></line>
                            </svg>
                        </div>
                        <h3 class="ai-sidebar-title">AI医学助手</h3>
                    </div>
                    <div class="ai-header-actions">
                        <button class="ai-sidebar-clear" id="ai-sidebar-clear">
                            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="8" y1="6" x2="21" y2="6"></line>
                                <line x1="8" y1="12" x2="21" y2="12"></line>
                                <line x1="8" y1="18" x2="21" y2="18"></line>
                                <line x1="3" y1="6" x2="3.01" y2="6"></line>
                                <line x1="3" y1="12" x2="3.01" y2="12"></line>
                                <line x1="3" y1="18" x2="3.01" y2="18"></line>
                            </svg>
                        </button>
                        <button class="ai-sidebar-close" id="ai-sidebar-close">&times;</button>
                    </div>
                </div>
                <div class="ai-sidebar-content">
                    <div class="ai-chat-container" id="ai-chat-container">
                        <div class="ai-chat-message ai">
                             你好！我是医学AI助手，有什么我可以帮助你的吗？
                        </div>
                    </div>
                    <form class="ai-chat-input-form" id="ai-chat-form">
                        <textarea 
                            class="ai-chat-input" 
                            id="ai-message-input" 
                            placeholder="输入您的问题或健康需求..." 
                            rows="3"
                        ></textarea>
                        <div class="ai-input-actions">
                            <span class="ai-input-hint">按 Ctrl+Enter 快速发送</span>
                            <button type="submit" class="ai-chat-send" id="ai-send-btn">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <line x1="22" y1="2" x2="11" y2="13"></line>
                                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                                </svg>
                                发送
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        try {
            // 添加到页面
            if (document.body) {
                document.body.appendChild(sidebar);
                console.log('侧边栏已添加到页面');
            } else {
                throw new Error('document.body不存在，无法添加侧边栏');
            }

            // 保存DOM引用
            this.elements = {
                toggle: document.getElementById('ai-sidebar-toggle'),
                panel: document.getElementById('ai-sidebar-panel'),
                close: document.getElementById('ai-sidebar-close'),
                clearBtn: document.getElementById('ai-sidebar-clear'), // 获取清除按钮引用
                form: document.getElementById('ai-chat-form'),
                input: document.getElementById('ai-message-input'),
                chatContainer: document.getElementById('ai-chat-container'),
                sendBtn: document.getElementById('ai-send-btn')
            };
        } catch (error) {
            console.error('创建侧边栏DOM元素失败:', error);
            // 重置elements对象
            this.elements = {
                toggle: null,
                panel: null,
                close: null,
                clearBtn: null,
                form: null,
                input: null,
                chatContainer: null,
                sendBtn: null
            };
        }
    }

    /**
     * 绑定事件处理函数
     */
    bindEvents() {
        // 切换侧边栏显示/隐藏
        if (this.elements.toggle) {
            // 使用箭头函数确保this上下文正确
            const toggleHandler = () => {
                console.log('侧边栏切换按钮被点击');
                this.toggleSidebar();
            };
            
            // 移除可能存在的旧事件监听器
            this.elements.toggle.removeEventListener('click', toggleHandler);
            // 添加新的事件监听器
            this.elements.toggle.addEventListener('click', toggleHandler);
            console.log('切换按钮事件已绑定');
        } else {
            console.error('切换按钮元素不存在，无法绑定点击事件');
        }

        if (this.elements.close) {
            const closeHandler = () => {
                console.log('侧边栏关闭按钮被点击');
                this.hideSidebar();
            };
            
            this.elements.close.removeEventListener('click', closeHandler);
            this.elements.close.addEventListener('click', closeHandler);
        }

        // 清除对话历史按钮事件
        if (this.elements.clearBtn) {
            const clearHandler = () => {
                console.log('清除对话历史按钮被点击');
                this.clearChatHistory();
            };
            
            this.elements.clearBtn.removeEventListener('click', clearHandler);
            this.elements.clearBtn.addEventListener('click', clearHandler);
        }

        // 表单提交处理
        if (this.elements.form) {
            const formHandler = (e) => {
                e.preventDefault();
                console.log('表单提交事件触发');
                this.handleSendMessage();
            };
            
            this.elements.form.removeEventListener('submit', formHandler);
            this.elements.form.addEventListener('submit', formHandler);
        }

        // 输入框按键事件 - 支持Ctrl+Enter发送消息
        if (this.elements.input) {
            const inputHandler = (e) => {
                if (e.ctrlKey && e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    console.log('Ctrl+Enter按键事件触发');
                    this.handleSendMessage();
                }
                // 自动调整文本框高度
                this.adjustInputHeight();
            };
            
            this.elements.input.removeEventListener('keydown', inputHandler);
            this.elements.input.addEventListener('keydown', inputHandler);
            
            // 输入变化时也调整高度
            this.elements.input.addEventListener('input', () => {
                this.adjustInputHeight();
            });
        }
    }

    /**
     * 自动调整输入框高度
     */
    adjustInputHeight() {
        if (this.elements.input) {
            this.elements.input.style.height = 'auto'; // 重置高度
            const scrollHeight = this.elements.input.scrollHeight;
            // 限制最大高度
            const maxHeight = 120; // 最大高度为120px
            const newHeight = Math.min(scrollHeight, maxHeight);
            this.elements.input.style.height = `${newHeight}px`;
        }
    }

    /**
     * 切换侧边栏显示状态
     */
    toggleSidebar() {
        if (!this.elements.panel) {
            console.error('侧边栏面板元素不存在');
            return;
        }
        
        console.log('切换侧边栏显示状态前:', this.elements.panel.classList.contains('active'));
        this.elements.panel.classList.toggle('active');
        console.log('切换侧边栏显示状态后:', this.elements.panel.classList.contains('active'));
        
        // 添加过渡动画效果类
        if (this.elements.panel.classList.contains('active')) {
            console.log('侧边栏已显示');
            // 聚焦输入框，提升用户体验
            if (this.elements.input) {
                setTimeout(() => this.elements.input.focus(), 300);
            }
        } else {
            console.log('侧边栏已隐藏');
        }
    }

    /**
     * 隐藏侧边栏
     */
    hideSidebar() {
        if (this.elements.panel) {
            this.elements.panel.classList.remove('active');
        }
    }

    /**
     * 处理发送消息
     */
    async handleSendMessage() {
        if (!this.elements.input || !this.elements.sendBtn) {
            console.error('输入框或发送按钮不存在');
            return;
        }
        
        const message = this.elements.input.value.trim();
        if (!message || this.isProcessing) return;

        // 清空输入框
        this.elements.input.value = '';
        this.adjustInputHeight(); // 重置输入框高度

        // 添加用户消息到UI
        this.addMessageToUI('user', message);

        // 显示加载状态
        this.isProcessing = true;
        this.elements.sendBtn.disabled = true;
        this.elements.sendBtn.innerHTML = `
            <svg class="loading-spinner" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="12" y1="2" x2="12" y2="6"></line>
                <line x1="12" y1="18" x2="12" y2="22"></line>
                <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
                <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
                <line x1="2" y1="12" x2="6" y2="12"></line>
                <line x1="18" y1="12" x2="22" y2="12"></line>
                <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
                <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
            </svg>
            思考中
        `;

        try {
            // 调用DeepSeek API获取回复
            const response = await getAIResponse(message);

            // 添加AI回复到UI
            this.addMessageToUI('ai', response);
        } catch (error) {
            console.error('AI回复出错:', error);
            this.addMessageToUI('ai', `抱歉，获取AI回复失败: ${error.message || '未知错误'}`);
            if (typeof showNotification === 'function') {
                showNotification('AI回复失败，请稍后再试', 'error');
            }
        } finally {
            // 恢复发送按钮状态
            this.isProcessing = false;
            this.elements.sendBtn.disabled = false;
            this.elements.sendBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
                发送
            `;
        }
    }

    /**
     * 将消息添加到UI
     */
    addMessageToUI(sender, content) {
        if (!this.elements.chatContainer) {
            console.error('聊天容器不存在');
            return;
        }
        
        // 创建消息元素
        const messageEl = document.createElement('div');
        messageEl.className = `ai-chat-message ${sender}`;
        messageEl.setAttribute('data-timestamp', new Date().toISOString());
        
        // 处理消息内容，支持简单的格式化显示
        const formattedContent = this.formatMessage(content);
        messageEl.innerHTML = formattedContent;

        // 添加消息动画效果
        messageEl.style.opacity = '0';
        messageEl.style.transform = 'translateY(10px)';
        messageEl.style.transition = 'opacity 0.3s ease, transform 0.3s ease';

        // 添加到聊天容器
        this.elements.chatContainer.appendChild(messageEl);

        // 触发重排然后应用动画
        setTimeout(() => {
            messageEl.style.opacity = '1';
            messageEl.style.transform = 'translateY(0)';
        }, 10);

        // 滚动到底部
        this.elements.chatContainer.scrollTop = this.elements.chatContainer.scrollHeight;

        // 保存消息到历史
        this.messages.push({ sender, content, timestamp: new Date() });
    }
    
    /**
     * 格式化消息内容
     */
    formatMessage(content) {
        // 简单的文本格式化，将换行符转换为<br>标签
        // 可根据需要扩展更多格式化功能
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*(.*?)\*/g, '<strong>$1</strong>'); // 将 *粗体* 转换为<strong>标签
    }

    /**
     * 清除对话历史
     */
    clearChatHistory() {
        if (!this.elements.chatContainer) {
            console.error('聊天容器不存在');
            return;
        }
        
        console.log('清除对话历史');
        
        // 清空消息数组
        this.messages = [];
        
        // 清空聊天容器内容
        this.elements.chatContainer.innerHTML = '';
        
        // 添加欢迎消息
        const welcomeMessage = document.createElement('div');
        welcomeMessage.className = 'ai-chat-message ai';
        welcomeMessage.textContent = '你好！我是医学AI助手，有什么我可以帮助你的吗？';
        this.elements.chatContainer.appendChild(welcomeMessage);
        
        // 显示通知
        if (typeof showNotification === 'function') {
            showNotification('对话历史已清除', 'success');
        }
    }
}

// 初始化函数
function initializeAISidebar() {
    try {
        console.log('AI侧边栏模块加载中...');

        // 检查模块依赖
        if (modules.allFailed) {
            throw new Error('核心依赖模块缺失');
        }

        // 创建实例并保存到全局变量
        aiSidebarInstance = new AISidebar();
        window.aiSidebar = aiSidebarInstance;
        console.log('window.aiSidebar已创建');

        // 检查页面是否应该初始化侧边栏
        function shouldInitializeAISidebar() {
            // 更健壮的页面检测方式
            const isLoginPage = window.location.pathname.includes('login.html') || 
                               window.location.pathname.includes('4 login.html');
            const isRegisterPage = window.location.pathname.includes('register.html') || 
                                 window.location.pathname.includes('8 register.html');
            
            const shouldInit = !isLoginPage && !isRegisterPage;
            console.log('是否应该初始化AI侧边栏:', shouldInit, '当前页面:', window.location.pathname);
            return shouldInit;
        }

        // 检查DOM是否已加载完成
        if (document.readyState === 'loading') {
            console.log('DOM尚未加载完成，等待DOMContentLoaded事件...');
            document.addEventListener('DOMContentLoaded', () => {
                console.log('DOMContentLoaded事件触发');
                if (shouldInitializeAISidebar()) {
                    console.log('调用window.aiSidebar.init()');
                    window.aiSidebar.init();
                }
            });
        } else {
            console.log('DOM已加载完成，直接检查初始化条件');
            if (shouldInitializeAISidebar()) {
                console.log('立即调用window.aiSidebar.init()');
                window.aiSidebar.init();
            }
        }

        // 添加手动初始化方法，方便调试
        window.initializeAISidebar = function() {
            console.log('手动调用初始化AI侧边栏');
            if (window.aiSidebar) {
                window.aiSidebar.init();
            } else {
                console.error('window.aiSidebar未定义，尝试重新创建实例');
                aiSidebarInstance = new AISidebar();
                window.aiSidebar = aiSidebarInstance;
                window.aiSidebar.init();
            }
        };

        return aiSidebarInstance;
    } catch (error) {
        console.error('❌ AI侧边栏模块加载失败:', error);
        // 在控制台创建一个全局错误变量，方便调试
        window.aiSidebarError = error;
        return null;
    }
}

// 当页面加载完成后初始化，确保DOM可用
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM完全加载后初始化AI侧边栏模块');
        initializeAISidebar();
    });
} else {
    console.log('页面已加载，立即初始化AI侧边栏模块');
    initializeAISidebar();
}

// 在模块顶层导出实例
export default aiSidebarInstance;
console.log('AI侧边栏模块导出完成');

// 添加全局调试函数，方便手动测试
window.debugAISidebar = function() {
    console.log('=== AI侧边栏调试信息 ===');
    console.log('侧边栏实例存在:', typeof window.aiSidebar !== 'undefined');
    console.log('侧边栏已初始化:', window.aiSidebar?.isInitialized || false);
    console.log('DOM元素状态:', window.aiSidebar?.elements || '无');
    console.log('是否有错误:', window.aiSidebarError || '无');
    console.log('========================');
    
    // 尝试手动显示侧边栏进行测试
    if (window.aiSidebar && window.aiSidebar.elements?.panel) {
        console.log('手动切换侧边栏显示状态');
        window.aiSidebar.elements.panel.classList.toggle('active');
    } else if (window.aiSidebar) {
        console.log('侧边栏存在但面板元素缺失，尝试重新初始化');
        window.aiSidebar.init();
    } else {
        console.log('侧边栏实例不存在，尝试创建新实例');
        initializeAISidebar();
    }
};

// 添加全局诊断函数，用于更深入的问题排查
window.diagnoseAISidebar = function() {
    console.log('=== AI侧边栏深度诊断 ===');
    
    // 检查核心模块
    console.log('核心模块检查:');
    console.log('- getAIResponse:', typeof getAIResponse);
    console.log('- showNotification:', typeof showNotification);
    console.log('- initAIModule:', typeof initAIModule);
    
    // 检查DOM结构
    console.log('\nDOM结构检查:');
    console.log('- document.body:', !!document.body);
    console.log('- 现有侧边栏:', document.querySelector('.ai-sidebar') ? '存在' : '不存在');
    
    // 检查API密钥配置
    console.log('\nAPI密钥配置:');
    const apiKey = sessionStorage.getItem('deepseekApiKey');
    console.log('- API密钥是否存在:', !!apiKey);
    
    // 检查当前页面
    console.log('\n当前页面信息:');
    console.log('- pathname:', window.location.pathname);
    console.log('- 应该初始化:', !window.location.pathname.includes('login.html') && 
                                !window.location.pathname.includes('register.html'));
    
    console.log('========================');
};
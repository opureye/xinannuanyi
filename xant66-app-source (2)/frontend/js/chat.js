/**
 * 聊天核心功能模块
 * 负责消息处理、对话历史管理和UI交互
 */
class ChatManager {
    constructor() {
        // DOM元素引用
        this.elements = {
            chatForm: document.getElementById('chat-form'),
            messageInput: document.getElementById('message-input'),
            chatContainer: document.getElementById('chat-container'),
            typingIndicator: document.getElementById('typing-indicator'),
            chatHistory: document.getElementById('chat-history'),
            newChatBtn: document.getElementById('new-chat-btn')
        };

        // 配置和状态
        this.config = null;
        this.currentChatId = null;
        this.chatHistoryData = [];
        this.isProcessing = false;

        // API配置
        this.apiConfig = {
            baseUrl: window.location.origin,
            timeout: 30000
        };

        // 初始化
        this.init();
    }

    /**
     * 初始化聊天管理器
     */
    async init() {
        try {
            // 加载配置
            await this.loadConfig();
            
            // 加载本地存储的对话历史
            this.loadChatHistory();
            
            // 绑定事件处理程序
            this.bindEvents();
            
            // 初始化UI
            this.renderChatHistory();
            
            // 如果有历史对话，默认加载第一个
            if (this.chatHistoryData.length > 0) {
                this.loadChat(this.chatHistoryData[0].id);
            }
            
            // 聚焦到输入框
            this.elements.messageInput.focus();
        } catch (error) {
            console.error('初始化聊天系统失败:', error);
            this.addMessageToUI('ai', `抱歉，系统初始化失败: ${error.message}`, true);
        }
    }

    /**
     * 加载配置文件
     */
    async loadConfig() {
        try {
            const response = await fetch('config.json');
            this.config = await response.json();
        } catch (error) {
            console.error('加载配置文件失败，使用默认配置:', error);
            // 使用默认配置
            this.config = {
                chat: {
                    maxHistoryCount: 50,
                    defaultTemperature: 0.7,
                    defaultMaxTokens: 1024,
                    showTimestamps: true,
                    enableAutoScroll: true
                }
            };
        }
    }

    /**
     * 绑定事件处理程序
     */
    bindEvents() {
        // 表单提交事件
        this.elements.chatForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        
        // 新对话按钮事件
        this.elements.newChatBtn.addEventListener('click', () => this.startNewChat());
        
        // 输入框按键事件 - 支持Ctrl+Enter发送消息
        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                this.handleFormSubmit(e);
            }
        });
    }

    /**
     * 处理表单提交
     */
    handleFormSubmit(e) {
        if (e) e.preventDefault();
        
        // 如果正在处理中，不允许发送新消息
        if (this.isProcessing) return;
        
        const message = this.elements.messageInput.value.trim();
        if (!message) return;
        
        // 处理消息发送
        this.sendMessage(message);
    }

    /**
     * 发送消息并处理回复
     */
    async sendMessage(message) {
        // 更新状态和UI
        this.isProcessing = true;
        this.elements.messageInput.value = '';
        this.elements.messageInput.disabled = true;
        
        // 显示用户消息
        this.addMessageToUI('user', message);
        
        // 管理对话历史
        if (!this.currentChatId) {
            this.createNewChatRecord(message);
        } else {
            this.updateChatRecord(message, 'user');
        }
        
        try {
            // 显示正在输入状态
            this.showTypingIndicator(true);
            
            // 获取AI回复 - 直接调用后端API
            let response;
            try {
                response = await this.getAIResponse(message);
            } catch (error) {
                console.error('获取AI回复失败:', error);
                // 显示错误信息给用户
                this.addMessageToUI('ai', `抱歉，出现错误: ${error.message}`, true);
                // 提前返回，不执行后续代码
                return;
            }
            
            // 显示AI回复
            this.addMessageToUI('ai', response);
            
            // 更新对话记录
            this.updateChatRecord(response, 'ai');
        } catch (error) {
            console.error('发送消息处理异常:', error);
            this.addMessageToUI('ai', `抱歉，出现系统错误`, true);
        } finally {
            // 恢复状态
            this.showTypingIndicator(false);
            this.isProcessing = false;
            this.elements.messageInput.disabled = false;
            this.elements.messageInput.focus();
        }
    }

    /**
     * 获取AI回复
     */
    async getAIResponse(message) {
        try {
            const response = await this.callBackendAPI();
            return response;
        } catch (error) {
            // 增强错误处理
            if (error.message.includes('NetworkError')) {
                throw new Error('网络连接异常，请检查您的网络连接');
            } else if (error.message.includes('404')) {
                throw new Error('API服务不可用，请确认后端服务已启动');
            } else if (error.message.includes('500')) {
                throw new Error('服务器内部错误，请稍后再试');
            }
            throw error;
        }
    }

    /**
     * 调用后端API（/api/ai/chat，与 AIChatBody：model + messages 一致）
     */
    async callBackendAPI() {
        const chat = this.chatHistoryData.find((c) => c.id === this.currentChatId);
        const messages = (chat && chat.messages
            ? chat.messages.map((m) => ({
                  role: m.sender === 'user' ? 'user' : 'assistant',
                  content: m.content
              }))
            : []
        );
        const model = this.config.defaultModel || 'deepseek-v3.2';

        const response = await fetch('/api/ai/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Accept: 'application/json'
            },
            body: JSON.stringify({
                model: model,
                messages: messages
            })
        });

        const raw = await response.text();
        let data = null;
        try {
            data = raw ? JSON.parse(raw) : null;
        } catch (e) {
            data = null;
        }

        if (!response.ok) {
            const detail = data && data.detail != null ? data.detail : null;
            const msg =
                typeof detail === 'string'
                    ? detail
                    : detail
                      ? JSON.stringify(detail)
                      : raw || `API请求失败 (${response.status})`;
            throw new Error(msg);
        }

        const text =
            data?.choices?.[0]?.message?.content ?? data?.response ?? null;
        if (text == null) {
            throw new Error('AI 返回格式异常');
        }
        return typeof text === 'string' ? text : String(text);
    }

    /**
     * 添加消息到UI
     */
    addMessageToUI(sender, content, isError = false) {
        // 创建消息元素
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex items-start message-enter ${sender === 'user' ? 'justify-end' : ''}`;
        
        // 获取当前时间
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // 设置消息内容
        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="max-w-[85%] bg-primary text-white p-4 rounded-lg rounded-tl-none shadow-sm">
                    <p class="message-content">${this.formatMessage(content)}</p>
                    ${this.config.chat.showTimestamps ? `<span class="timestamp">${timeString}</span>` : ''}
                </div>
                <div class="ml-3 w-8 h-8 rounded-full bg-neutral-300 flex-shrink-0 flex items-center justify-center">
                    <i class="fa fa-user text-neutral-600"></i>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="mr-3 w-8 h-8 rounded-full bg-primary flex-shrink-0 flex items-center justify-center">
                    <i class="fa fa-robot text-white"></i>
                </div>
                <div class="max-w-[85%] ${isError ? 'bg-red-100 text-red-800' : 'bg-white text-neutral-800'} p-4 rounded-lg rounded-tr-none shadow-sm">
                    <p class="message-content">${this.formatMessage(content)}</p>
                    ${this.config.chat.showTimestamps ? `<span class="timestamp">${timeString}</span>` : ''}
                </div>
            `;
        }
        
        // 添加到聊天容器
        this.elements.chatContainer.appendChild(messageDiv);
        
        // 自动滚动到底部
        if (this.config.chat.enableAutoScroll) {
            this.scrollToBottom();
        }
        
        return messageDiv;
    }

    /**
     * 格式化消息内容
     */
    formatMessage(content) {
        // 替换换行符为<br>
        let formatted = content.replace(/\n/g, '<br>');
        
        // 简单检测并替换链接
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        formatted = formatted.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
        
        return formatted;
    }

    /**
     * 显示/隐藏正在输入指示器
     */
    showTypingIndicator(show) {
        if (show) {
            this.elements.typingIndicator.classList.remove('hidden');
        } else {
            this.elements.typingIndicator.classList.add('hidden');
        }
    }

    /**
     * 滚动到聊天底部
     */
    scrollToBottom() {
        this.elements.chatContainer.scrollTop = this.elements.chatContainer.scrollHeight;
    }

    /**
     * 开始新对话
     */
    startNewChat() {
        this.currentChatId = null;
        
        // 清空聊天容器
        this.elements.chatContainer.innerHTML = `
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
        
        // 更新UI
        this.renderChatHistory();
        
        // 聚焦到输入框
        this.elements.messageInput.focus();
    }

    /**
     * 创建新的对话记录
     */
    createNewChatRecord(firstMessage) {
        const chatId = Date.now().toString();
        const chatTitle = firstMessage.length > 30 
            ? firstMessage.substring(0, 30) + '...' 
            : firstMessage;
            
        const newChat = {
            id: chatId,
            title: chatTitle,
            timestamp: new Date().toISOString(),
            messages: [
                { sender: 'user', content: firstMessage, timestamp: new Date().toISOString() }
            ]
        };
        
        // 更新当前对话ID
        this.currentChatId = chatId;
        
        // 添加到历史记录
        this.chatHistoryData.unshift(newChat);
        
        // 限制历史记录数量
        if (this.chatHistoryData.length > this.config.chat.maxHistoryCount) {
            this.chatHistoryData = this.chatHistoryData.slice(0, this.config.chat.maxHistoryCount);
        }
        
        // 保存到本地存储
        this.saveChatHistory();
        
        // 更新UI
        this.renderChatHistory();
    }

    /**
     * 更新对话记录
     */
    updateChatRecord(content, sender) {
        const chatIndex = this.chatHistoryData.findIndex(chat => chat.id === this.currentChatId);
        if (chatIndex !== -1) {
            // 添加新消息
            this.chatHistoryData[chatIndex].messages.push({
                sender: sender,
                content: content,
                timestamp: new Date().toISOString()
            });
            
            // 如果是用户的第一条消息，更新标题
            if (sender === 'user' && this.chatHistoryData[chatIndex].messages.length === 1) {
                this.chatHistoryData[chatIndex].title = content.length > 30 
                    ? content.substring(0, 30) + '...' 
                    : content;
            }
            
            // 保存到本地存储
            this.saveChatHistory();
            
            // 更新UI
            this.renderChatHistory();
        }
    }

    /**
     * 从本地存储加载对话历史
     */
    loadChatHistory() {
        try {
            const stored = localStorage.getItem('chatHistory');
            if (stored) {
                this.chatHistoryData = JSON.parse(stored);
            }
        } catch (error) {
            console.error('加载对话历史失败:', error);
            this.chatHistoryData = [];
        }
    }

    /**
     * 保存对话历史到本地存储
     */
    saveChatHistory() {
        try {
            localStorage.setItem('chatHistory', JSON.stringify(this.chatHistoryData));
        } catch (error) {
            console.error('保存对话历史失败:', error);
        }
    }

    /**
     * 渲染对话历史列表
     */
    renderChatHistory() {
        // 清空现有列表
        this.elements.chatHistory.innerHTML = '';
        
        // 添加所有对话
        this.chatHistoryData.forEach(chat => {
            const li = document.createElement('li');
            li.innerHTML = `
                <button class="w-full text-left p-3 rounded-lg ${this.currentChatId === chat.id ? 'bg-primary/10 text-neutral-800' : 'bg-neutral-100 text-neutral-700'} hover:bg-primary/20 transition-colors flex items-start space-x-3 chat-history-item">
                    <i class="fa fa-comment-o mt-1 ${this.currentChatId === chat.id ? 'text-primary' : 'text-neutral-500'}"></i>
                    <span class="truncate">${chat.title}</span>
                </button>
            `;
            
            // 添加点击事件
            li.querySelector('button').addEventListener('click', () => {
                this.loadChat(chat.id);
            });
            
            this.elements.chatHistory.appendChild(li);
        });
    }

    /**
     * 加载特定对话
     */
    loadChat(chatId) {
        const chat = this.chatHistoryData.find(c => c.id === chatId);
        if (chat) {
            // 更新当前对话ID
            this.currentChatId = chatId;
            
            // 清空聊天容器
            this.elements.chatContainer.innerHTML = '';
            
            // 添加所有消息
            chat.messages.forEach(message => {
                this.addMessageToUI(message.sender, message.content);
            });
            
            // 更新历史列表UI
            this.renderChatHistory();
            
            // 在移动设备上关闭侧边栏
            if (window.innerWidth <= 768) {
                const sidebar = document.getElementById('sidebar');
                const overlay = document.querySelector('.overlay');
                sidebar.classList.remove('active');
                overlay.classList.remove('active');
            }
        }
    }
}

// 当DOM加载完成后初始化聊天管理器
document.addEventListener('DOMContentLoaded', () => {
    // 创建全局实例，方便其他脚本访问
    window.chatManager = new ChatManager();
});

/**
 * SDK工具模块 - 封装和管理第三方SDK的初始化和配置
 */

/**
 * AI工具模块 - 管理AI相关功能和配置
 */

// 存储AI个人访问令牌
let aiAccessToken = '';

/**
 * 更新AI个人访问令牌
 * @param {string} newToken - 新的个人访问令牌
 * @returns {boolean} - 更新是否成功
 */
export function updateAIAccessToken(newToken) {
    if (newToken && typeof newToken === 'string' && newToken.trim()) {
        aiAccessToken = newToken.trim();
        sessionStorage.setItem('deepseekApiKey', aiAccessToken);
        console.log('DeepSeek API密钥已更新');
        return true;
    }
    console.error('无效的DeepSeek API密钥');
    return false;
}

/**
 * 获取当前的AI个人访问令牌
 * @returns {string} - 当前的个人访问令牌
 */
export function getAIAccessToken() {
    // 优先从sessionStorage获取
    if (!aiAccessToken) {
        aiAccessToken = sessionStorage.getItem('deepseekApiKey') || '';
    }
    return aiAccessToken;
}

/**
 * 初始化AI功能模块
 */
export function initAIModule() {
    // 从sessionStorage加载API密钥
    const savedKey = sessionStorage.getItem('deepseekApiKey');
    
    if (savedKey) {
        aiAccessToken = savedKey;
    } else {
        // 初始化时不设置默认API密钥
        aiAccessToken = '';
        console.log('AI模块初始化完成，未设置默认API密钥');
    }
    
    console.log('AI模块初始化完成');
    return true;
}

// 将函数挂载到window对象，使其在全局可用
window.aiUtils = {
    updateAIAccessToken,
    getAIAccessToken,
    initAIModule
};
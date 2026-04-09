// 导入共享的SDK工具模块
import { updateAIAccessToken, initAIModule } from './sdk_utils.js';

// 处理令牌更新表单
function handleTokenUpdate() {
  const tokenInput = document.querySelector('.token-input');
  const submitBtn = document.querySelector('.submit-btn');
  
  if (tokenInput && submitBtn) {
    submitBtn.addEventListener('click', function() {
      const newToken = tokenInput.value.trim();
      
      if (newToken) {
        // 实际更新令牌
        const updateSuccess = updateAIAccessToken(newToken);
        
        if (updateSuccess) {
          // 显示成功消息
          alert('DeepSeek API密钥已更新！');
          tokenInput.value = '';
          
          // 尝试重新初始化SDK以应用新令牌
          try {
            const moduleInitialized = initAIModule();
            if (moduleInitialized) {
              console.log('AI模块已使用新密钥重新初始化');
            }
          } catch (error) {
            console.error('重新初始化AI模块失败:', error);
          }
        } else {
          alert('更新密钥失败，请检查密钥格式');
        }
      } else {
        alert('请输入有效的API密钥');
      }
    });
  }
}

// 页面加载完成后初始化
function initPage() {
  // 初始化AI模块
  initAIModule();
  
  // 初始化表单处理
  handleTokenUpdate();
}

// 页面加载完成后执行初始化
window.addEventListener('DOMContentLoaded', initPage);
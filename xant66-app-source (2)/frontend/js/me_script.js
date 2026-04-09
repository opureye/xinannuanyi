// 修复me_script.js中的导入问题
// 移除对不存在的initCozeSDK函数的导入
// 如果这个文件不需要任何SDK功能，可以完全清空
// 如果需要使用AI功能，可以导入正确存在的函数
import { getAIAccessToken, initAIModule } from './sdk_utils.js';
import { initReloginButtons } from './auth.js';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
  // 如果需要初始化AI模块
  initAIModule();
  
  // 初始化重新登录按钮的事件处理
  initReloginButtons();
  
  // 其他页面相关的逻辑可以在这里添加
  // 例如，处理position_demo元素
  const positionDemo = document.getElementById('position_demo');
  if (positionDemo) {
    positionDemo.innerHTML = '版权所有：浙江传媒学院"信安暖驿"项目组  2025-2026  版本：alpha-4.0<br>' +
      '📮 邮箱：<a href="mailto:HongshengyueJeff@163.com" class="contact">HongshengyueJeff@163.com</a>　' +
      '💬 QQ交流群：<a href="https://qm.qq.com/q/saS8pBFeN2" target="_blank" class="contact">1045970841</a>';
  }

  const slider = document.querySelector('.intro-slider .slides');
  if (slider) {
    let index = 0;
    const count = slider.children.length;
    setInterval(() => {
      index = (index + 1) % count;
      slider.style.transform = `translateX(-${index * 100}%)`;
    }, 3000);
  }
});
/**
 * 设置表单提交处理
 */
function setupFormSubmission() {
    const complaintForm = document.querySelector('form');
    if (complaintForm) {
        complaintForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // 获取表单数据
            const targetName = document.getElementById('author-name').value;
            const complaintReason = document.getElementById('complaint-reason').value;
            
            // 验证表单数据
            if (!validateForm(targetName, complaintReason)) {
                showNotification('请填写完整的举报信息', 'error');
                return;
            }
            
            // 显示提交中状态
            const submitBtn = document.querySelector('.submit-btn');
            submitBtn.disabled = true;
            submitBtn.textContent = '提交中...';
            
            // 模拟提交过程
            simulateSubmission(targetName, complaintReason)
                .then(() => {
                    // 提交成功
                    showNotification('举报已成功提交，感谢您的反馈', 'success');
                    // 重置表单
                    complaintForm.reset();
                })
                .catch(error => {
                    // 提交失败
                    showNotification('提交失败，请稍后重试', 'error');
                    console.error('Submission error:', error);
                })
                .finally(() => {
                    // 恢复按钮状态
                    submitBtn.disabled = false;
                    submitBtn.textContent = '提交举报';
                });
        });
    }
}

/**
 * 验证表单数据
 * @param {string} targetName - 举报目标
 * @param {string} complaintReason - 举报理由
 * @returns {boolean} - 是否验证通过
 */
function validateForm(targetName, complaintReason) {
    if (!targetName || targetName.trim().length === 0) {
        return false;
    }
    
    if (!complaintReason || complaintReason.trim().length < 10) {
        return false;
    }
    
    return true;
}

/**
 * 设置表单验证
 */
function setupFormValidation() {
    const inputs = document.querySelectorAll('input, textarea');
    
    inputs.forEach(input => {
        // 实时验证
        input.addEventListener('input', function() {
            validateField(this);
        });
        
        // 失去焦点时验证
        input.addEventListener('blur', function() {
            validateField(this);
        });
    });
}

/**
 * 验证单个字段
 * @param {HTMLElement} field - 表单字段
 */
function validateField(field) {
    const errorMessage = field.nextElementSibling;
    
    if (field.hasAttribute('required') && !field.value.trim()) {
        if (errorMessage && errorMessage.classList.contains('error-message')) {
            errorMessage.textContent = '此字段为必填项';
            errorMessage.style.display = 'block';
        }
        field.classList.add('invalid');
    } else if (field.id === 'complaint-reason' && field.value.length < 10) {
        if (errorMessage && errorMessage.classList.contains('error-message')) {
            errorMessage.textContent = '请至少输入10个字符';
            errorMessage.style.display = 'block';
        }
        field.classList.add('invalid');
    } else {
        if (errorMessage && errorMessage.classList.contains('error-message')) {
            errorMessage.style.display = 'none';
        }
        field.classList.remove('invalid');
    }
}

/**
 * 模拟表单提交过程
 * @param {string} targetName - 举报目标
 * @param {string} complaintReason - 举报理由
 * @returns {Promise} - 提交结果
 */
function simulateSubmission(targetName, complaintReason) {
    return new Promise((resolve, reject) => {
        // 模拟网络延迟
        setTimeout(() => {
            // 模拟成功率90%
            const isSuccess = Math.random() < 0.9;
            if (isSuccess) {
                console.log('举报信息:', {
                    targetName,
                    complaintReason,
                    timestamp: new Date().toISOString()
                });
                resolve();
            } else {
                reject(new Error('Network error'));
            }
        }, 1500);
    });
}

/**
 * 显示通知信息
 * @param {string} message - 通知消息
 * @param {string} type - 通知类型（success, error, info）
 */
function showNotification(message, type = 'info') {
    // 检查是否已存在通知元素
    let notification = document.getElementById('notification');
    if (notification) {
        document.body.removeChild(notification);
    }
    
    // 创建新的通知元素
    notification = document.createElement('div');
    notification.id = 'notification';
    notification.textContent = message;
    
    // 设置基础样式
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.left = '50%';
    notification.style.transform = 'translateX(-50%)';
    notification.style.padding = '15px 30px';
    notification.style.borderRadius = '25px';
    notification.style.color = 'white';
    notification.style.fontWeight = '500';
    notification.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.2)';
    notification.style.zIndex = '9999';
    notification.style.opacity = '0';
    notification.style.transition = 'opacity 0.3s, transform 0.3s';
    notification.style.transform = 'translate(-50%, -20px)';
    notification.style.textAlign = 'center';
    
    // 根据类型设置不同背景色
    switch(type) {
        case 'success':
            notification.style.backgroundColor = '#27ae60';
            break;
        case 'error':
            notification.style.backgroundColor = '#e74c3c';
            break;
        case 'info':
        default:
            notification.style.backgroundColor = '#3498db';
            break;
    }
    
    document.body.appendChild(notification);
    
    // 显示通知
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translate(-50%, 0)';
    }, 10);
    
    // 3秒后隐藏通知
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translate(-50%, -20px)';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

/**
 * 添加表单动画效果
 */
function addFormAnimations() {
    const formGroups = document.querySelectorAll('.form-group');
    
    formGroups.forEach((group, index) => {
        // 为每个表单组添加延迟动画
        group.style.opacity = '0';
        group.style.transform = 'translateY(20px)';
        group.style.transition = `opacity 0.3s ease, transform 0.3s ease`;
        
        setTimeout(() => {
            group.style.opacity = '1';
            group.style.transform = 'translateY(0)';
        }, 100 + (index * 100));
    });
}
// 等待DOM内容加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 获取表单元素
    const registerForm = document.getElementById('registerForm');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    // 实名认证弹窗元素
    const realnameModal = document.getElementById('realnameModal');
    const realNameInput = document.getElementById('realNameInput');
    const idNumberInput = document.getElementById('idNumberInput');
    const cancelVerifyBtn = document.getElementById('cancelVerifyBtn');
    const confirmVerifyBtn = document.getElementById('confirmVerifyBtn');
    
    // 表单提交处理
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            if (!validateForm()) return;

            // 显示实名认证弹窗
            openModal();
        });
    }
    
    // 添加密码匹配检查
    if (passwordInput && confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            validatePasswordMatch();
        });
        
        passwordInput.addEventListener('input', function() {
            validatePasswordMatch();
        });
    }
    
    // 表单验证函数
    function validateForm() {
        // 检查密码是否匹配
        if (!validatePasswordMatch()) {
            return false;
        }
        
        // 可以添加其他验证逻辑，如手机号格式、邮箱格式等
        // 例如手机号验证
        const phoneInput = document.getElementById('phone');
        if (phoneInput) {
            const phoneRegex = /^1[3-9]\d{9}$/;
            if (!phoneRegex.test(phoneInput.value)) {
                alert('请输入有效的手机号码');
                phoneInput.focus();
                return false;
            }
        }
        
        // 例如邮箱验证
        const emailInput = document.getElementById('email');
        if (emailInput) {
            const emailRegex = /^[^@]+@[^@]+\.[^@]+$/;
            if (!emailRegex.test(emailInput.value)) {
                alert('请输入有效的电子邮箱地址');
                emailInput.focus();
                return false;
            }
        }
        
        return true;
    }
    
    // 密码匹配验证函数
    function validatePasswordMatch() {
        // 只有当两个框都有值时才进行实时校验提示，避免干扰输入
        if (passwordInput.value && confirmPasswordInput.value) {
             if (passwordInput.value !== confirmPasswordInput.value) {
                confirmPasswordInput.setCustomValidity('两次输入的密码不匹配');
                // 移除 reportValidity()，避免输入过程中焦点跳动
                // confirmPasswordInput.reportValidity(); 
                return false;
            } else {
                confirmPasswordInput.setCustomValidity('');
                return true;
            }
        }
        // 如果其中一个为空，先不报错，等待用户输完
        confirmPasswordInput.setCustomValidity('');
        return true;
    }

    // 弹窗控制
    function openModal() {
        if (realnameModal) {
            realnameModal.style.display = 'flex';
            realNameInput && realNameInput.focus();
        }
    }
    function closeModal() {
        if (realnameModal) {
            realnameModal.style.display = 'none';
        }
    }

    if (cancelVerifyBtn) {
        cancelVerifyBtn.addEventListener('click', function() {
            closeModal();
        });
    }

    if (confirmVerifyBtn) {
        confirmVerifyBtn.addEventListener('click', async function() {
            const name = (realNameInput?.value || '').trim();
            const idNo = (idNumberInput?.value || '').trim().toUpperCase();
            if (!name || !idNo) {
                alert('请输入姓名和身份证号');
                return;
            }
            try {
                const verifyResp = await fetch('/api/identity/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, id_number: idNo })
                });
                const verifyResult = await verifyResp.json();

                // 统一从原始回包中提取友好提示，避免出现 [object Object]
                let allowRegister = false;
                let friendlyMsg = '';

                const provider = verifyResult?.provider || '';
                const detail = verifyResult?.detail || null;
                const raw = (detail && typeof detail === 'object') ? detail.raw : null;

                if (provider === 'Tencent' && raw) {
                    const resultCode = String(raw?.Result ?? '').trim();
                    const description = raw?.Description || verifyResult?.message || '实名认证结果未知';
                    allowRegister = (resultCode === '0');
                    friendlyMsg = description;
                } else {
                    // 本地或其他模式的兜底处理
                    allowRegister = !!verifyResult?.success;
                    const maybeText = (typeof verifyResult?.detail === 'string') ? verifyResult.detail : '';
                    friendlyMsg = maybeText || verifyResult?.message || (allowRegister ? '实名认证通过' : '实名认证失败');
                }

                if (!verifyResp.ok || !allowRegister) {
                    alert(friendlyMsg);
                    return;
                }

                // 通过核验后提交注册
                const formData = {
                    username: document.getElementById('nickname').value,
                    phone: document.getElementById('phone').value,
                    email: document.getElementById('email').value,
                    password: document.getElementById('password').value,
                    // 将实名信息一并提交后端写库
                    real_name: name,
                    id_number: idNo
                };
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                const result = await response.json();
                if (response.ok && result.success) {
                    alert(result.message || friendlyMsg || '注册成功！');
                    closeModal();
                    window.location.href = '4 login.html';
                } else {
                    const errorMessage = result.detail || result.message || '注册失败，请稍后重试';
                    alert(errorMessage);
                }
            } catch (error) {
                console.error('实名认证或注册流程失败:', error);
                alert('网络异常，请稍后重试');
            }
        });
    }
});
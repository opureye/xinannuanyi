import sqlite3
import json
from config import settings
from utils.db_users_utils import users_db

# 获取用户123的完整密码哈希
conn = sqlite3.connect(settings.db_path)
cursor = conn.cursor()
cursor.execute('SELECT password_hash FROM users WHERE username = ?', ('123',))
result = cursor.fetchone()
conn.close()

if result:
    password_hash = result[0]
    print('=== 用户123的密码哈希数据 ===')
    print(f'完整哈希: {password_hash}')
    
    try:
        password_data = json.loads(password_hash)
        print(f'版本: {password_data.get("version")}')
        print(f'模式: {password_data.get("mode")}')
        print(f'盐: {password_data.get("salt")}')
        print(f'随机数: {password_data.get("nonce")}')
        print(f'密文: {password_data.get("ciphertext")}')
        
        # 检查系统密钥
        print(f'\n=== 系统密钥信息 ===')
        print(f'私钥存在: {hasattr(users_db, "private_key")}')
        if hasattr(users_db, 'private_key'):
            print(f'私钥长度: {len(users_db.private_key)}')
            print(f'私钥前10字符: {users_db.private_key[:10]}')
        
        # 尝试手动解密过程
        print(f'\n=== 手动解密测试 ===')
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            
            # 派生加密密钥
            salt = password_data['salt'].encode('utf-8')
            encryption_key = users_db._kdf(users_db.private_key.encode('utf-8'), salt, b'password_encryption', 32)
            print(f'加密密钥派生成功，长度: {len(encryption_key)}')
            
            # 创建AES-GCM对象
            aesgcm = AESGCM(encryption_key)
            nonce = bytes.fromhex(password_data['nonce'])
            ciphertext = bytes.fromhex(password_data['ciphertext'])
            
            print(f'随机数长度: {len(nonce)}')
            print(f'密文长度: {len(ciphertext)}')
            
            # 尝试解密
            decrypted = aesgcm.decrypt(nonce, ciphertext, None)
            decrypted_password = decrypted.decode('utf-8')
            print(f'解密成功！原始密码: {decrypted_password}')
            
            # 验证密码
            if decrypted_password == '123456':
                print('密码匹配！')
            else:
                print(f'密码不匹配，期望: 123456，实际: {decrypted_password}')
                
        except Exception as e:
            print(f'手动解密失败: {str(e)}')
            import traceback
            traceback.print_exc()
            
    except json.JSONDecodeError as e:
        print(f'JSON解析失败: {str(e)}')
else:
    print('未找到用户123')

# 测试创建新密码哈希
print(f'\n=== 测试创建新密码哈希 ===')
try:
    new_hash = users_db._hash_password('123456')
    print(f'新密码哈希: {new_hash}')
    
    # 测试新哈希的验证
    verify_result = users_db._check_password('123456', new_hash)
    print(f'新哈希验证结果: {verify_result}')
except Exception as e:
    print(f'创建新哈希失败: {str(e)}')
    import traceback
    traceback.print_exc()
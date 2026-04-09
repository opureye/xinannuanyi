from utils.db_users_utils import users_db
import sqlite3
from config import settings

print('=== 修复admin用户的密码 ===')

# 首先检查admin用户是否存在
conn = sqlite3.connect(settings.db_path)
cursor = conn.cursor()
cursor.execute('SELECT username FROM users WHERE username = ?', ('admin',))
admin_user = cursor.fetchone()
conn.close()

if not admin_user:
    print('admin用户不存在，正在创建...')
    try:
        # 创建admin用户
        result = users_db.add_user('admin', 'admin123', 'admin@example.com', '管理员')
        print(f'创建admin用户结果: {result}')
    except Exception as e:
        print(f'创建admin用户失败: {str(e)}')

# 为admin用户重新设置密码为admin123
try:
    # 生成新的密码哈希
    new_password_hash = users_db._hash_password('admin123')
    print(f'新密码哈希: {new_password_hash}')
    
    # 更新数据库中的密码哈希
    conn = sqlite3.connect(settings.db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_password_hash, 'admin'))
    conn.commit()
    conn.close()
    
    print('密码哈希更新成功！')
    
    # 测试新密码
    result = users_db.verify_user('admin', 'admin123')
    print(f'验证结果: {result}')
    
    if result[0]:
        print('✓ admin用户的密码修复成功！现在可以使用密码"admin123"登录')
    else:
        print('✗ 密码修复失败')
        
except Exception as e:
    print(f'修复过程中出现错误: {str(e)}')
    import traceback
    traceback.print_exc()
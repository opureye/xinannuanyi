from utils.db_users_utils import users_db
import sqlite3
from config import settings

# 测试所有用户的密码验证
conn = sqlite3.connect(settings.db_path)
cursor = conn.cursor()
cursor.execute('SELECT username FROM users')
users = cursor.fetchall()
conn.close()

print('=== 测试所有用户的密码验证 ===')
test_passwords = ['123456', '123', 'password', 'admin']

for user in users:
    username = user[0]
    print(f'\n用户: {username}')
    for pwd in test_passwords:
        try:
            result = users_db.verify_user(username, pwd)
            if result[0]:  # 如果验证成功
                print(f'  密码 "{pwd}": 成功 ✓')
                break
            else:
                print(f'  密码 "{pwd}": {result[1]}')
        except Exception as e:
            print(f'  密码 "{pwd}": 错误 - {str(e)}')
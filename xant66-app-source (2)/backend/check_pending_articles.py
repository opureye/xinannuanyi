import sqlite3
import os

# 连接数据库
db_path = os.path.join(os.path.dirname(__file__), 'database', 'forum.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查待审核帖子数量
cursor.execute('SELECT COUNT(*) FROM articles WHERE status = "pending"')
pending_count = cursor.fetchone()[0]
print(f'待审核帖子数量: {pending_count}')

# 检查所有帖子的状态分布
cursor.execute('SELECT status, COUNT(*) FROM articles GROUP BY status')
status_counts = cursor.fetchall()
print('\n所有帖子状态分布:')
for status, count in status_counts:
    print(f'{status}: {count}')

# 查看待审核帖子详情
cursor.execute('SELECT id, title, author, status, created_at FROM articles WHERE status = "pending" LIMIT 10')
articles = cursor.fetchall()
print('\n待审核帖子列表:')
if articles:
    for article in articles:
        print(f'ID: {article[0]}, 标题: {article[1]}, 作者: {article[2]}, 状态: {article[3]}, 创建时间: {article[4]}')
else:
    print('没有找到待审核的帖子')

# 查看最近的帖子
cursor.execute('SELECT id, title, author, status, created_at FROM articles ORDER BY created_at DESC LIMIT 5')
recent_articles = cursor.fetchall()
print('\n最近的帖子:')
for article in recent_articles:
    print(f'ID: {article[0]}, 标题: {article[1]}, 作者: {article[2]}, 状态: {article[3]}, 创建时间: {article[4]}')

conn.close()
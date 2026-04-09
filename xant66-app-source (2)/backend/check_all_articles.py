import sqlite3
import json

# 连接数据库
conn = sqlite3.connect('database/forum.db')
cursor = conn.cursor()

# 查询所有待审核文章
cursor.execute('SELECT id, title, content, author, created_at, status FROM articles WHERE status = "pending" ORDER BY created_at DESC')
pending_articles = cursor.fetchall()

print('=== 数据库中所有待审核文章 ===')
print(f'总数: {len(pending_articles)}')
print()

for article in pending_articles:
    print(f'ID: {article[0]}')
    print(f'标题: {article[1]}')
    print(f'内容预览: {article[2][:100]}...' if len(article[2]) > 100 else f'内容: {article[2]}')
    print(f'作者: {article[3]}')
    print(f'创建时间: {article[4]}')
    print(f'状态: {article[5]}')
    print('-' * 50)

# 查询所有文章状态分布
cursor.execute('SELECT status, COUNT(*) FROM articles GROUP BY status')
status_counts = cursor.fetchall()

print('\n=== 文章状态分布 ===')
for status, count in status_counts:
    print(f'{status}: {count}篇')

# 查询最近的几篇文章（不限状态）
cursor.execute('SELECT id, title, status, created_at FROM articles ORDER BY created_at DESC LIMIT 10')
recent_articles = cursor.fetchall()

print('\n=== 最近的10篇文章 ===')
for article in recent_articles:
    print(f'ID: {article[0]}, 标题: {article[1]}, 状态: {article[2]}, 时间: {article[3]}')

conn.close()
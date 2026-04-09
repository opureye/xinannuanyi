import sqlite3

db_path = r'c:\Users\94954\Desktop\xant6.4\backend\database\forum.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('SELECT status, COUNT(*) FROM articles GROUP BY status')
print('状态分布:')
for s, c in cursor.fetchall():
    print(f'  {s}: {c}')

cursor.execute('SELECT id, title, author, status FROM articles ORDER BY id DESC LIMIT 5')
print('\n最近帖子:')
for a in cursor.fetchall():
    print(f'ID:{a[0]} 标题:{a[1][:15]}... 作者:{a[2]} 状态:{a[3]}')

conn.close()

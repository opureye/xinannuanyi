# 数据库增强功能文档

本文档介绍新增的数据库安全、性能和功能增强模块。

## 1. SQL注入防护模块 (`sql_security.py`)

### 功能概述
提供输入验证、清理和安全的SQL查询构建功能，防止SQL注入攻击。

### 主要类和方法

#### SQLSecurityValidator
- `validate_string()`: 验证字符串输入，检测SQL关键字和危险模式
- `sanitize_string()`: 清理字符串输入，移除危险字符
- `validate_integer()`: 验证整数输入
- `validate_table_name()`: 验证表名（只允许字母、数字和下划线）
- `validate_column_name()`: 验证列名

#### SafeQueryBuilder
- `build_where_clause()`: 安全地构建WHERE子句
- `build_order_clause()`: 安全地构建ORDER BY子句

### 使用示例
```python
from backend.utils.sql_security import SQLSecurityValidator, SafeQueryBuilder, SQLOperator

# 验证输入
is_valid, error = SQLSecurityValidator.validate_string(user_input)
if not is_valid:
    raise ValueError(error)

# 清理搜索输入
search_term = validate_search_input(search_query)

# 构建安全查询
conditions = [
    ("status", SQLOperator.EQUALS, "approved"),
    ("title", SQLOperator.LIKE, f"%{search_term}%")
]
where_clause, params = SafeQueryBuilder.build_where_clause(conditions)
```

## 2. 数据库连接池和锁机制 (`db_locker.py`)

### 功能概述
提供线程安全的数据库连接管理和锁功能，防止多并发查询出现问题。

### 主要类

#### DatabaseConnectionPool
- 管理数据库连接池
- 自动创建和回收连接
- 支持超时控制

#### DatabaseLock
- 读锁（共享锁）：允许多个读操作并发
- 写锁（排他锁）：确保写操作的独占性
- 事务锁：支持多表事务

### 使用示例
```python
from backend.utils.db_locker import DatabaseConnectionPool, DatabaseLock

# 创建连接池
pool = DatabaseConnectionPool(db_path, pool_size=5)

# 使用连接
with pool.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")

# 使用锁
lock_manager = DatabaseLock()
with lock_manager.write_lock("users", timeout=10.0):
    # 执行写操作
    cursor.execute("UPDATE users SET ...")
```

### 装饰器
```python
from backend.utils.db_locker import with_db_lock

@with_db_lock(lock_type="write", tables=["users"], timeout=10.0)
def update_user(user_id, data):
    # 自动获取写锁
    pass
```

## 3. 跨表查询功能 (`db_join_queries.py`)

### 功能概述
提供安全的JOIN查询封装，简化跨表查询操作。

### 主要类

#### JoinQueryBuilder
- `join_tables()`: 执行多表JOIN查询
- `get_user_with_articles()`: 获取用户及其文章（示例方法）
- `get_article_with_comments()`: 获取文章及其评论（示例方法）
- `get_user_achievements_with_details()`: 获取用户成就详细信息（示例方法）

### 使用示例
```python
from backend.utils.db_join_queries import JoinQueryBuilder

builder = JoinQueryBuilder(connection)

# 自定义JOIN查询
results = builder.join_tables(
    main_table="users",
    join_clauses=[
        ("articles", JoinQueryBuilder.JoinType.LEFT, "users.id", "articles.author_id", "a")
    ],
    select_columns=["users.username", "a.title", "a.created_at"],
    where_conditions=[("users.id", "=", user_id)],
    limit=10
)

# 使用预定义方法
user_articles = builder.get_user_with_articles(user_id=1)
```

## 4. 增强的成就系统 (`db_achievements_enhanced.py`)

### 功能概述
提供更完善的成就系统，包括更多成就类型和自动解锁机制。

### 主要类

#### AchievementManager
- `check_and_unlock_achievements()`: 检查并自动解锁用户应得的成就
- `get_user_achievements()`: 获取用户的所有成就
- `get_user_achievement_statistics()`: 获取用户成就统计信息

### 预定义成就类型
1. **发帖相关**: 初出茅庐、文思泉涌、笔耕不辍、著作等身
2. **点赞相关**: 初获青睐、备受喜爱、人气爆棚、万人追捧
3. **粉丝相关**: 小有名气、初具规模、声名鹊起、大V认证
4. **等级相关**: 初窥门径、登堂入室、炉火纯青、登峰造极
5. **评论相关**: 初次发言、积极互动、评论达人
6. **收藏相关**: 收藏家、收藏大师
7. **实用文章**: 实用专家、知识分享者
8. **特殊成就**: 新手上路、每日签到

### 使用示例
```python
from backend.utils.db_achievements_enhanced import AchievementManager

# 初始化成就管理器
achievement_manager = AchievementManager(db._get_connection)

# 检查并解锁成就（通常在用户操作后调用）
unlocked = achievement_manager.check_and_unlock_achievements(user_id)
for achievement in unlocked:
    print(f"解锁成就: {achievement['title']}")

# 获取用户成就
achievements = achievement_manager.get_user_achievements(user_id)

# 获取统计信息
stats = achievement_manager.get_user_achievement_statistics(user_id)
```

## 5. 集成模块 (`db_integration.py`)

### 功能概述
提供统一的接口来初始化和使用所有增强功能。

### 主要函数

#### initialize_database_features()
初始化数据库的所有增强功能（连接池、成就管理器等）。

### 使用示例
```python
from backend.utils.db_integration import initialize_database_features

# 在数据库初始化时调用
initialize_database_features(db, enable_pool=True, pool_size=5)
```

## 6. 数据库核心类更新 (`db_core.py`)

### 新增方法
- `enable_connection_pool()`: 启用连接池
- `disable_connection_pool()`: 禁用连接池
- `_get_connection()`: 已更新，支持连接池

## 7. 安全性改进

### SQL注入防护
- 所有用户输入都经过验证和清理
- 使用参数化查询
- 列名和表名验证
- 危险字符检测

### 并发控制
- 连接池管理
- 读写锁机制
- 事务锁支持
- 超时控制

## 注意事项

1. **连接池**: 默认启用连接池，大小为5。可根据实际需求调整。

2. **锁机制**: 使用锁时要避免死锁，建议：
   - 按表名排序获取多表锁
   - 设置合理的超时时间
   - 尽快释放锁

3. **成就系统**: 成就条件评估使用简单的字符串解析，不支持复杂的表达式。如需复杂条件，建议使用数据库触发器或定期任务。

4. **性能**: 
   - WAL模式提高了并发性能
   - 连接池减少了连接创建开销
   - 锁机制确保数据一致性

## 迁移指南

现有代码无需修改即可使用新功能，因为：
1. 向后兼容：所有原有方法保持不变
2. 可选启用：新功能需要显式启用
3. 渐进式采用：可以逐步采用新功能

## 示例：完整使用流程

```python
# 1. 初始化数据库
from backend.utils.database import db
from backend.utils.db_integration import initialize_database_features

# 启用增强功能
initialize_database_features(db, enable_pool=True, pool_size=5)

# 2. 使用SQL注入防护
from backend.utils.sql_security import validate_search_input, SQLSecurityValidator

search_term = validate_search_input(user_input)

# 3. 使用锁机制执行写操作
from backend.utils.db_locker import DatabaseLock

lock_manager = DatabaseLock()
with lock_manager.write_lock("articles", timeout=10.0):
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO articles ...")

# 4. 使用跨表查询
from backend.utils.db_join_queries import JoinQueryBuilder

builder = JoinQueryBuilder(db._get_connection())
results = builder.get_user_with_articles(user_id=1)

# 5. 检查成就
if hasattr(db, 'achievement_manager'):
    unlocked = db.achievement_manager.check_and_unlock_achievements(user_id)
```


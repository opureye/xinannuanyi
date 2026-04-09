# 数据库模块 - 整合所有数据库功能
import logging
import sqlite3  # 添加sqlite3导入
from .db_users_core import ExtendedUserDatabase as UserDatabase  # 修复：从db_users_core导入正确的类
from .db_users import (
    users_db,
    verify_user,
    add_user,
    get_user_by_username,
    get_user_count,
    update_user_profile,
    get_user_profile
)
from .sample_users_initializer import SampleUserInitializer  # 添加这一行
from .db_articles import (
    articles_db,
    add_article,
    get_article_by_id,
    get_pending_articles,
    update_article_status,
    search_articles,
    delete_article_and_related_data,
    add_complaint,
    get_complained_articles,
    get_complaints_by_article
)
from .db_comments import (
    comments_db,
    add_comment,
    get_comments_by_article,
    toggle_comment_like,
    add_comment_complaint,
    get_complained_comments,
    get_complaints_by_comment,
    update_comment_status
)
from .db_follows import (
    follows_db,
    follow_user,
    unfollow_user,
    get_user_following,
    get_user_followers,
    is_following
)
# 添加收藏功能模块
from .db_collections import (
    collections_db,
    add_collection,
    remove_collection,
    get_user_collections,
    is_article_collected,
    get_user_collection_count,
    get_collected_articles_by_user
)
# 添加配置导入
from backend.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_sample_users_if_needed():
    """只在需要时初始化示例用户"""
    logger.info("开始初始化示例用户...")
    initializer = SampleUserInitializer()
    initializer.initialize_sample_users()

# 创建统一的数据库实例
logger.info(f"创建主数据库实例，使用路径: {settings.db_path}")
db = UserDatabase(settings.db_path)

# 启用数据库增强功能（连接池、锁机制等）
try:
    from .db_integration import initialize_database_features
    initialize_database_features(db, enable_pool=True, pool_size=5)
except Exception as e:
    logger.warning(f"初始化数据库增强功能失败: {e}，将使用默认模式")

# 调用初始化函数创建必要的表
def init_follow_tables(db_instance):
    """初始化关注相关的表"""
    try:
        with db_instance._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建关注表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS follows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    follower TEXT NOT NULL,
                    following TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (follower) REFERENCES users (username),
                    FOREIGN KEY (following) REFERENCES users (username),
                    UNIQUE (follower, following)
                )
            ''')
            
            conn.commit()
            logger.info("关注表初始化成功")
    except Exception as e:
        logger.error(f"初始化关注表失败: {str(e)}")

# 用于初始化收藏表
def init_collection_tables():
    try:
        with db._get_connection() as conn:
            cursor = conn.cursor()
            # 创建收藏表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                article_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, article_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
            ''')
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"初始化收藏表失败: {str(e)}")

# 调用初始化函数创建必要的表
init_follow_tables(db)
init_collection_tables()

# 导出便捷函数
__all__ = [
    'db',
    'verify_user',
    'add_user',
    'get_user_by_username',
    'get_user_count',
    'update_user_profile',
    'get_user_profile',
    'add_article',
    'get_article_by_id',
    'get_pending_articles',
    'update_article_status',
    'search_articles',
    'delete_article_and_related_data',
    'add_complaint',
    'get_complained_articles',
    'get_complaints_by_article',
    'add_comment',
    'get_comments_by_article',
    'toggle_comment_like',
    'add_comment_complaint',
    'get_complained_comments',
    'get_complaints_by_comment',
    'update_comment_status',
    'follow_user',
    'unfollow_user',
    'get_user_following',
    'get_user_followers',
    'is_following',
    # 添加收藏功能相关函数
    'add_collection',
    'remove_collection',
    'get_user_collections',
    'is_article_collected',
    'get_user_collection_count',
    'get_collected_articles_by_user',
    # 添加缺失的函数
    'get_all_users',
    'search_users',
    'deactivate_user'
]

# 为了保持向后兼容性，重新定义原来的便捷函数
def verify_user_login(username, password):
    return verify_user(username, password)

def get_user_info(username):
    return get_user_by_username(username)

# 在文件底部添加这个函数
def initialize_sample_users():
    """初始化示例用户"""
    initializer = SampleUserInitializer()
    initializer.initialize_sample_users()

# 修改get_all_users函数，确保包含role和status字段
def get_all_users():
    """获取所有用户信息"""
    try:
        with db._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email, phone, avatar, bio, level, experience, posts_count, fans_count, likes_count, helpful_posts_count, created_at, updated_at, last_login, status, role FROM users"
            )
            users = cursor.fetchall()
            return [dict(user) for user in users]
    except sqlite3.Error as e:
        logger.error(f"获取所有用户失败: {str(e)}")
        return []

# 修改search_users函数，确保包含role和status字段
def search_users(keyword):
    """搜索用户"""
    try:
        with db._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email, phone, avatar, bio, level, experience, posts_count, fans_count, likes_count, helpful_posts_count, created_at, updated_at, last_login, status, role FROM users WHERE username LIKE ? OR email LIKE ?",
                (f"%{keyword}%", f"%{keyword}%")
            )
            users = cursor.fetchall()
            return [dict(user) for user in users]
    except sqlite3.Error as e:
        logger.error(f"搜索用户失败: {str(e)}")
        return []


def deactivate_user(username):
    """停用用户"""
    try:
        with db._get_connection() as conn:
            cursor = conn.cursor()
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if not cursor.fetchone():
                logger.warning(f"用户不存在: {username}")
                return False
            
            # 在这个实现中，我们通过设置特殊标记来"停用"用户
            cursor.execute("UPDATE users SET bio = '此用户已被停用' WHERE username = ?", (username,))
            conn.commit()
            logger.info(f"用户已停用: {username}")
            return True
    except sqlite3.Error as e:
        logger.error(f"停用用户失败: {str(e)}")
        return False

# 添加封禁用户函数
def ban_user(username):
    """封禁用户，使其无法登录"""
    try:
        with db._get_connection() as conn:
            cursor = conn.cursor()
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if not cursor.fetchone():
                logger.warning(f"用户不存在: {username}")
                return False
            
            # 更新用户状态为封禁
            cursor.execute("UPDATE users SET status = 'banned' WHERE username = ?", (username,))
            conn.commit()
            logger.info(f"用户已封禁: {username}")
            
            # 清除被封禁用户的所有现有会话
            from utils.auth import session_manager
            for session_id, session_data in list(session_manager.sessions.items()):
                if session_data.username == username:
                    session_manager.destroy_session(session_id)
                    logger.info(f"已清除被封禁用户 {username} 的会话: {session_id[:8]}...")
            
            return True
    except sqlite3.Error as e:
        logger.error(f"封禁用户失败: {str(e)}")
        return False

# 添加解封用户函数
def unban_user(username):
    """解封用户，恢复其登录权限"""
    try:
        with db._get_connection() as conn:
            cursor = conn.cursor()
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if not cursor.fetchone():
                logger.warning(f"用户不存在: {username}")
                return False
            
            # 更新用户状态为活跃
            cursor.execute("UPDATE users SET status = 'active' WHERE username = ?", (username,))
            conn.commit()
            logger.info(f"用户已解封: {username}")
            return True
    except sqlite3.Error as e:
        logger.error(f"解封用户失败: {str(e)}")
        return False

# 在ban_user函数后添加delete_user函数

def delete_user(username):
    """从数据库中永久删除用户"""
    try:
        with db._get_connection() as conn:
            cursor = conn.cursor()
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if not cursor.fetchone():
                logger.warning(f"用户不存在: {username}")
                return False
            
            # 先删除用户的相关数据（文章、评论、收藏等）
            cursor.execute("DELETE FROM articles WHERE author = ?", (username,))
            cursor.execute("DELETE FROM comments WHERE user_id = ?", (username,))
            cursor.execute("DELETE FROM collections WHERE user_id = ?", (username,))
            cursor.execute("DELETE FROM follows WHERE follower = ? OR following = ?", (username, username))
            cursor.execute("DELETE FROM complaints WHERE reporter = ?", (username,))
            
            # 然后删除用户本身
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()
            logger.info(f"用户已被永久删除: {username}")
            return True
    except sqlite3.Error as e:
        logger.error(f"删除用户失败: {str(e)}")
        return False

# 关注功能数据库操作模块
import logging
from typing import List, Dict, Any
import sqlite3
from backend.config import settings  # 添加settings导入
from .db_core import UserDatabase

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建数据库实例
class FollowDatabase(UserDatabase):
    def __init__(self, db_path=None):
        # 如果未提供db_path，则使用配置中的路径
        db_path = db_path if db_path else settings.db_path
        super().__init__(db_path)
        # 确保关注表存在
        self._init_follow_tables()
        
    def _init_follow_tables(self):
        """初始化关注相关数据表"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 创建关注表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS follows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    follower_id INTEGER NOT NULL,
                    following_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(follower_id, following_id),
                    FOREIGN KEY (follower_id) REFERENCES users(id),
                    FOREIGN KEY (following_id) REFERENCES users(id)
                )
                ''')
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"初始化关注表失败: {str(e)}")

# 创建数据库实例
_db_instance = FollowDatabase(settings.db_path)  # 使用settings.db_path初始化
# 保持原有的follows_db变量名
follows_db = _db_instance
# 添加db别名，确保与其他模块保持一致
if 'db' not in locals():
    db = _db_instance

# 关注功能方法
def follow_user(follower_username: str, following_username: str) -> Dict[str, Any]:
    """
    关注用户
    
    :param follower_username: 粉丝用户名
    :param following_username: 被关注用户名
    :return: 操作结果
    """
    try:
        if follower_username == following_username:
            return {"success": False, "message": "不能关注自己"}
            
        with follows_db._get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查用户是否存在
            cursor.execute("SELECT username FROM users WHERE username = ?", (follower_username,))
            follower = cursor.fetchone()
            if not follower:
                return {"success": False, "message": "粉丝用户不存在"}
            
            cursor.execute("SELECT username FROM users WHERE username = ?", (following_username,))
            following = cursor.fetchone()
            if not following:
                return {"success": False, "message": "被关注用户不存在"}
            
            # 检查是否已经关注
            cursor.execute(
                "SELECT * FROM follows WHERE follower = ? AND following = ?", 
                (follower_username, following_username)
            )
            if cursor.fetchone():
                return {"success": False, "message": "已经关注该用户"}
            
            # 添加关注关系
            cursor.execute(
                "INSERT INTO follows (follower, following) VALUES (?, ?)", 
                (follower_username, following_username)
            )
            
            # 更新粉丝数
            cursor.execute(
                "UPDATE users SET fans_count = fans_count + 1 WHERE username = ?", 
                (following_username,)
            )
            
            conn.commit()
            return {"success": True, "message": f"成功关注 {following_username}"}
    except Exception as e:
        logger.error(f"关注用户失败: {str(e)}")
        return {"success": False, "message": f"关注失败: {str(e)}"}


def unfollow_user(follower_username: str, following_username: str) -> Dict[str, Any]:
    """
    取消关注用户
    
    :param follower_username: 粉丝用户名
    :param following_username: 被关注用户名
    :return: 操作结果
    """
    try:
        with follows_db._get_connection() as conn:  # 更新为使用follows_db
            cursor = conn.cursor()
            
            # 检查是否已关注
            cursor.execute(
                "SELECT * FROM follows WHERE follower = ? AND following = ?", 
                (follower_username, following_username)
            )
            if not cursor.fetchone():
                return {"success": False, "message": "还未关注该用户"}
                
            # 删除关注关系
            cursor.execute(
                "DELETE FROM follows WHERE follower = ? AND following = ?", 
                (follower_username, following_username)
            )
            
            # 更新粉丝数
            cursor.execute(
                "UPDATE users SET fans_count = fans_count - 1 WHERE username = ?", 
                (following_username,)
            )
            
            conn.commit()
            return {"success": True, "message": f"成功取消关注 {following_username}"}
    except Exception as e:
        logger.error(f"取消关注用户失败: {str(e)}")
        return {"success": False, "message": f"取消关注失败: {str(e)}"}


def get_user_following(username: str) -> List[Dict[str, Any]]:
    """
    获取用户关注的所有人
    
    :param username: 用户名
    :return: 关注列表
    """
    try:
        with follows_db._get_connection() as conn:  # 更新为使用follows_db
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 查询用户关注的人
            cursor.execute('''
                SELECT u.username, u.avatar, u.bio, f.created_at 
                FROM follows f 
                JOIN users u ON f.following = u.username 
                WHERE f.follower = ? 
                ORDER BY f.created_at DESC
            ''', (username,))
            
            following_list = []
            for row in cursor.fetchall():
                following_list.append({
                    "username": row["username"],
                    "avatar": row["avatar"],
                    "bio": row["bio"],
                    "followed_at": row["created_at"]
                })
            
            return following_list
    except Exception as e:
        logger.error(f"获取关注列表失败: {str(e)}")
        return []


def get_user_followers(username: str) -> List[Dict[str, Any]]:
    """
    获取用户的所有粉丝
    
    :param username: 用户名
    :return: 粉丝列表
    """
    try:
        with follows_db._get_connection() as conn:  # 更新为使用follows_db
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 查询关注该用户的粉丝
            cursor.execute('''
                SELECT u.username, u.avatar, u.bio, f.created_at 
                FROM follows f 
                JOIN users u ON f.follower = u.username 
                WHERE f.following = ? 
                ORDER BY f.created_at DESC
            ''', (username,))
            
            followers_list = []
            for row in cursor.fetchall():
                followers_list.append({
                    "username": row["username"],
                    "avatar": row["avatar"],
                    "bio": row["bio"],
                    "followed_at": row["created_at"]
                })
            
            return followers_list
    except Exception as e:
        logger.error(f"获取粉丝列表失败: {str(e)}")
        return []


def is_following(follower_username: str, following_username: str) -> bool:
    """
    检查用户是否已关注另一个用户
    
    :param follower_username: 粉丝用户名
    :param following_username: 被关注用户名
    :return: 是否已关注
    """
    try:
        with follows_db._get_connection() as conn:  # 更新为使用follows_db
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT 1 FROM follows WHERE follower = ? AND following = ?", 
                (follower_username, following_username)
            )
            
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"检查关注状态失败: {str(e)}")
        return False

# 导出便捷函数
__all__ = [
    'db',
    'follows_db',
    'follow_user',
    'unfollow_user',
    'get_user_following',
    'get_user_followers',
    'is_following'
]

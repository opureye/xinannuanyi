import sqlite3
# 从core模块导入ExtendedUserDatabase基类
from .db_users_core import ExtendedUserDatabase, logger

def get_user_post_count(self, user_id: int) -> int:
    """
    获取用户的帖子数量
    
    :param user_id: 用户ID
    :return: 帖子数量
    """
    try:
        # 根据user_id获取用户名
        user = self.get_user_by_id(user_id)
        if not user:
            return 0
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 修复：将author_id改为author（使用用户名）
            cursor.execute("SELECT COUNT(*) FROM articles WHERE author = ?", (user['username'],))
            count = cursor.fetchone()[0]
            return count
    except sqlite3.Error as e:
        logger.error(f"获取用户帖子数量失败: {str(e)}")
        return 0

def get_user_collection_count(self, user_id: int) -> int:
    """
    获取用户的收藏数量
    
    :param user_id: 用户ID
    :return: 收藏数量
    """
    try:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM collections WHERE user_id = ?", (user_id,))
            count = cursor.fetchone()[0]
            return count
    except sqlite3.Error as e:
        logger.error(f"获取用户收藏数量失败: {str(e)}")
        return 0

def get_user_followers_count(self, user_id: int) -> int:
    """
    获取用户的粉丝数量
    
    :param user_id: 用户ID
    :return: 粉丝数量
    """
    try:
        # 根据user_id获取用户名
        user = self.get_user_by_id(user_id)
        if not user:
            return 0
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM follows WHERE following = ?", (user['username'],))
            count = cursor.fetchone()[0]
            return count
    except sqlite3.Error as e:
        logger.error(f"获取用户粉丝数量失败: {str(e)}")
        return 0

def get_user_following_count(self, user_id: int) -> int:
    """
    获取用户关注的人数
    
    :param user_id: 用户ID
    :return: 关注人数
    """
    try:
        # 根据user_id获取用户名
        user = self.get_user_by_id(user_id)
        if not user:
            return 0
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM follows WHERE follower = ?", (user['username'],))
            count = cursor.fetchone()[0]
            return count
    except sqlite3.Error as e:
        logger.error(f"获取用户关注人数失败: {str(e)}")
        return 0

# 将方法绑定到ExtendedUserDatabase类
ExtendedUserDatabase.get_user_post_count = get_user_post_count
ExtendedUserDatabase.get_user_collection_count = get_user_collection_count
ExtendedUserDatabase.get_user_followers_count = get_user_followers_count
ExtendedUserDatabase.get_user_following_count = get_user_following_count
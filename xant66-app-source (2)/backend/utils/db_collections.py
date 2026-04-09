import sqlite3
import logging
from typing import Dict, Any, List
from .db_core import UserDatabase as CoreUserDatabase
from backend.config import settings

logger = logging.getLogger(__name__)

class UserDatabase(CoreUserDatabase):
    def __init__(self, db_path: str = None):
        # 如果未提供db_path，则使用配置中的路径
        db_path = db_path if db_path else settings.db_path
        super().__init__(db_path)
    
    def add_collection(self, username: str, article_id: int) -> bool:
        """
        添加收藏
        
        :param username: 用户名
        :param article_id: 文章ID
        :return: 添加是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查用户是否存在
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                if not cursor.fetchone():
                    logger.warning(f"用户不存在: {username}")
                    return False
                
                # 检查文章是否存在且已审核通过
                cursor.execute("SELECT id, status FROM articles WHERE id = ?", (article_id,))
                article = cursor.fetchone()
                if not article or article[1] != 'approved':
                    logger.warning(f"文章不存在或未审核通过: {article_id}")
                    return False
                
                # 添加收藏
                cursor.execute(
                    "INSERT OR IGNORE INTO collections (user_id, article_id) VALUES (?, ?)",
                    (username, article_id)
                )
                
                conn.commit()
                # 如果影响行数大于0，则说明添加成功（之前未收藏）
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"添加收藏失败: {str(e)}")
            return False
    
    def remove_collection(self, username: str, article_id: int) -> bool:
        """
        取消收藏
        
        :param username: 用户名
        :param article_id: 文章ID
        :return: 取消是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 删除收藏
                cursor.execute(
                    "DELETE FROM collections WHERE user_id = ? AND article_id = ?",
                    (username, article_id)
                )
                
                conn.commit()
                # 如果影响行数大于0，则说明删除成功（之前已收藏）
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"取消收藏失败: {str(e)}")
            return False
    
    def get_user_collections(self, username: str) -> List[Dict[str, Any]]:
        """
        获取用户的所有收藏
        
        :param username: 用户名
        :return: 收藏的文章列表
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 获取用户的所有收藏，关联文章表获取文章信息
                cursor.execute(
                    '''
                    SELECT a.id, a.title, a.content, a.author, a.updated_at, a.view_count, a.like_count, a.comment_count, c.created_at as collected_at
                    FROM collections c
                    JOIN articles a ON c.article_id = a.id
                    WHERE c.user_id = ? AND a.status = 'approved'
                    ORDER BY c.created_at DESC
                    ''',
                    (username,)
                )
                
                collections = cursor.fetchall()
                return [dict(item) for item in collections]
        except sqlite3.Error as e:
            logger.error(f"获取用户收藏失败: {str(e)}")
            return []
    
    def is_article_collected(self, username: str, article_id: int) -> bool:
        """
        检查用户是否已收藏指定文章
        
        :param username: 用户名
        :param article_id: 文章ID
        :return: 是否已收藏
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT id FROM collections WHERE user_id = ? AND article_id = ?",
                    (username, article_id)
                )
                
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"检查收藏状态失败: {str(e)}")
            return False
    
    def get_user_collection_count(self, username: str) -> int:
        """
        获取用户的收藏数量
        
        :param username: 用户名
        :return: 收藏数量
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT COUNT(*) FROM collections WHERE user_id = ?",
                    (username,)
                )
                
                count = cursor.fetchone()[0]
                return count
        except sqlite3.Error as e:
            logger.error(f"获取收藏数量失败: {str(e)}")
            return 0
    
    def get_collected_articles_by_user(self, username: str) -> List[int]:
        """
        获取用户收藏的所有文章ID
        
        :param username: 用户名
        :return: 文章ID列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT article_id FROM collections WHERE user_id = ?",
                    (username,)
                )
                
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"获取收藏文章ID列表失败: {str(e)}")
            return []

# 添加get_db函数的实现
def get_db():
    """获取数据库实例的便捷函数"""
    return collections_db

# 创建数据库实例
_db_instance = UserDatabase(settings.db_path)
# 保持原有的collections_db变量名
collections_db = _db_instance
# 添加db别名，确保与其他模块保持一致
if 'db' not in locals():
    db = _db_instance

# 修复便捷函数调用方式，统一使用collections_db
def add_collection(username: str, article_id: int) -> Dict[str, Any]:
    try:
        with collections_db._get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取用户ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if not user:
                return {"success": False, "message": "用户不存在"}
            user_id = user[0]
            
            # 检查文章是否存在
            cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
            if not cursor.fetchone():
                return {"success": False, "message": "文章不存在"}
            
            # 检查是否已经收藏
            cursor.execute(
                "SELECT * FROM collections WHERE user_id = ? AND article_id = ?", 
                (user_id, article_id)
            )
            if cursor.fetchone():
                return {"success": False, "message": "已经收藏该文章"}
            
            # 添加收藏
            cursor.execute(
                "INSERT INTO collections (user_id, article_id) VALUES (?, ?)", 
                (user_id, article_id)
            )
            
            conn.commit()
            return {"success": True, "message": "收藏成功"}
    except Exception as e:
        logger.error(f"添加收藏失败: {str(e)}")
        return {"success": False, "message": f"收藏失败: {str(e)}"}


def remove_collection(username: str, article_id: int) -> Dict[str, Any]:
    try:
        with collections_db._get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取用户ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if not user:
                return {"success": False, "message": "用户不存在"}
            user_id = user[0]
            
            # 检查是否已经收藏
            cursor.execute(
                "SELECT * FROM collections WHERE user_id = ? AND article_id = ?", 
                (user_id, article_id)
            )
            if not cursor.fetchone():
                return {"success": False, "message": "未收藏该文章"}
            
            # 移除收藏
            cursor.execute(
                "DELETE FROM collections WHERE user_id = ? AND article_id = ?", 
                (user_id, article_id)
            )
            
            conn.commit()
            return {"success": True, "message": "取消收藏成功"}
    except Exception as e:
        logger.error(f"移除收藏失败: {str(e)}")
        return {"success": False, "message": f"取消收藏失败: {str(e)}"}

def get_user_collections(username: str) -> List[Dict[str, Any]]:
    return collections_db.get_user_collections(username)

def is_article_collected(username: str, article_id: int) -> bool:
    return collections_db.is_article_collected(username, article_id)

def get_user_collection_count(username: str) -> int:
    return collections_db.get_user_collection_count(username)

def get_collected_articles_by_user(username: str) -> List[int]:
    return collections_db.get_collected_articles_by_user(username)

# 导出模块成员
__all__ = [
    'db',
    'collections_db',
    'get_db',
    'add_collection',
    'remove_collection',
    'get_user_collections',
    'is_article_collected',
    'get_user_collection_count',
    'get_collected_articles_by_user'
]

import os
import sqlite3
from typing import List, Dict, Any

# 直接在当前文件中定义CRYPTO_AVAILABLE变量
CRYPTO_AVAILABLE = False
try:
    from cryptography.hazmat.primitives.asymmetric import dh
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import serialization
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# 导入基础类
from .db_core import UserDatabase as CoreUserDatabase, logger
# 修复导入路径，改为直接导入config模块
import backend.config as config

# 扩展UserDatabase类，添加用户管理功能
class ExtendedUserDatabase(CoreUserDatabase):
    def __init__(self, db_path: str = None):
        # 如果未提供db_path，则使用配置中的路径
        db_path = db_path if db_path else config.settings.db_path
        super().__init__(db_path)
        logger.info(f"[db_users] 初始化UserDatabase，使用的数据库路径: {os.path.abspath(self.db_path)}")
        # 确保系统密钥可用
        if not hasattr(self, 'private_key'):
            logger.warning("系统私钥不存在，尝试重新加载")
            self._load_or_generate_system_keys()
    
    def get_user_posts(self, user_id: int, offset: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取用户的文章列表
        
        :param user_id: 用户ID
        :param offset: 偏移量
        :param limit: 限制数量
        :return: 用户文章列表
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 首先获取用户名
                cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
                user_result = cursor.fetchone()
                if not user_result:
                    logger.warning(f"用户ID {user_id} 不存在")
                    return []
                
                username = user_result['username']
                
                # 获取用户的文章
                cursor.execute(
                    """SELECT 
                        a.id as post_id,
                        a.title,
                        a.content,
                        a.category,
                        a.created_at,
                        a.status,
                        COALESCE(a.like_count, 0) as likes_count,
                        COALESCE(comments.comments_count, 0) as comments_count
                    FROM articles a
                    LEFT JOIN (
                        SELECT article_id, COUNT(*) as comments_count 
                        FROM comments 
                        GROUP BY article_id
                    ) comments ON a.id = comments.article_id
                    WHERE a.author = ?
                    ORDER BY a.created_at DESC
                    LIMIT ? OFFSET ?""",
                    (username, limit, offset)
                )
                
                posts = cursor.fetchall()
                return [dict(post) for post in posts]
                
        except sqlite3.Error as e:
            logger.error(f"获取用户文章失败: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"获取用户文章时发生未预期错误: {str(e)}", exc_info=True)
            return []
    
    def get_user_post_count(self, user_id: int) -> int:
        """
        获取用户文章总数
        
        :param user_id: 用户ID
        :return: 文章总数
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 首先获取用户名
                cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
                user_result = cursor.fetchone()
                if not user_result:
                    return 0
                
                username = user_result[0]
                
                # 获取文章总数
                cursor.execute("SELECT COUNT(*) FROM articles WHERE author = ?", (username,))
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except sqlite3.Error as e:
            logger.error(f"获取用户文章总数失败: {str(e)}")
            return 0
        except Exception as e:
            logger.error(f"获取用户文章总数时发生未预期错误: {str(e)}", exc_info=True)
            return 0

# 导入其他模块以确保方法绑定被执行
from . import db_users_basic
from . import db_users_admin
from . import db_users_relationships

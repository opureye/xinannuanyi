import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List
# 修复导入：从db_core导入UserDatabase并重命名为CoreUserDatabase
from .db_core import UserDatabase as CoreUserDatabase
from .logger import get_logger
from backend.config import settings

logger = get_logger(__name__)

class UserDatabase(CoreUserDatabase):
    def add_article(self, title: str, content: str, author_username: str, category: str) -> Optional[int]:
        """
        添加新文章到数据库并返回文章ID
        """
        try:
            logger.info(f"[DB操作] 开始添加文章 - 作者: {author_username}, 标题: '{title[:30]}...', 分类: {category}")
            
            # 检查作者是否存在
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE username = ?", (author_username,))
                author = cursor.fetchone()
                
                if not author:
                    logger.error(f"[DB操作失败] 添加文章时找不到作者 - 用户名: {author_username}")
                    return None
                
                author_id = author[0]
                
                # 插入文章记录
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    """INSERT INTO articles (title, content, author, category, created_at, updated_at, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (title, content, author_username, category, now, now, 'pending')
                )
                
                article_id = cursor.lastrowid
                conn.commit()
                
                # 更新用户文章计数
                cursor.execute(
                    "UPDATE users SET posts_count = posts_count + 1 WHERE id = ?",
                    (author_id,)
                )
                conn.commit()
                
                logger.info(f"[DB操作成功] 文章已成功添加 - ID: {article_id}, 作者ID: {author_id}")
                return article_id
        except sqlite3.Error as e:
            logger.error(f"[数据库错误] 添加文章时发生SQLite错误: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"[系统错误] 添加文章时发生未预期错误: {str(e)}", exc_info=True)
            return None
    def __init__(self, db_path: str = None):
        # 如果未提供db_path，则使用配置中的路径
        db_path = db_path if db_path else settings.db_path
        super().__init__(db_path)

    def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取文章信息
        """
        try:
            # 统一使用_get_connection方法
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT a.*, u.avatar, u.level FROM articles a JOIN users u ON a.author = u.username WHERE a.id = ?",
                    (article_id,)
                )
                article = cursor.fetchone()
                
                if article:
                    # 增加阅读计数
                    cursor.execute(
                        "UPDATE articles SET view_count = view_count + 1 WHERE id = ?",
                        (article_id,)
                    )
                    conn.commit()
                    return dict(article)
                
                return None
        except sqlite3.Error as e:
            logger.error(f"获取文章时发生错误: {str(e)}")
            return None

    def get_pending_articles(self) -> List[Dict[str, Any]]:
        """
        获取所有待审核的文章
        """
        try:
            # 统一使用_get_connection方法
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT a.*, u.avatar, u.level FROM articles a JOIN users u ON a.author = u.username WHERE a.status = 'pending' ORDER BY a.created_at DESC"
                )
                articles = cursor.fetchall()
                return [dict(article) for article in articles]
        except sqlite3.Error as e:
            logger.error(f"获取待审核文章时发生错误: {str(e)}")
            return []

    def update_article_status(self, article_id: int, status: str) -> bool:
        """
        更新文章的审核状态
        
        :param article_id: 文章ID
        :param status: 状态（'approved' 或 'rejected'）
        :return: 更新是否成功
        """
        if status not in ['approved', 'rejected']:
            logger.warning(f"无效的文章状态: {status}")
            return False
            
        try:
            if status == 'rejected':
                # 如果状态是rejected，删除文章及其相关数据
                return self.delete_article_and_related_data(article_id)
            else:
                # 否则更新状态为approved
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE articles SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (status, article_id)
                    )
                    conn.commit()
                    logger.info(f"成功更新文章状态: {article_id}，状态: {status}")
                    return True
        except sqlite3.Error as e:
            logger.error(f"更新文章状态失败: {str(e)}")
            return False

    def search_articles(self, keyword: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        搜索文章
        
        :param keyword: 搜索关键词
        :param limit: 返回结果数量限制
        :param offset: 结果偏移量
        :return: 匹配的文章列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 构建搜索条件
                search_term = f"%{keyword}%"
                
                cursor.execute(
                    "SELECT a.*, u.avatar, u.level FROM articles a JOIN users u ON a.author = u.username WHERE (a.title LIKE ? OR a.content LIKE ?) AND a.status = 'approved' ORDER BY a.created_at DESC LIMIT ? OFFSET ?",
                    (search_term, search_term, limit, offset)
                )
                articles = cursor.fetchall()
                return [dict(article) for article in articles]
        except sqlite3.Error as e:
            logger.error(f"搜索文章时发生错误: {str(e)}")
            return []

    def delete_article_and_related_data(self, article_id: int) -> bool:
        """
        删除文章及其相关数据（包括举报、互动等）
        
        :param article_id: 文章ID
        :return: 删除是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 开始事务
                conn.execute("BEGIN TRANSACTION")
                
                # 获取文章作者
                cursor.execute("SELECT author FROM articles WHERE id = ?", (article_id,))
                result = cursor.fetchone()
                if result:
                    author = result[0]
                    
                    # 删除相关的举报记录
                    cursor.execute("DELETE FROM complaints WHERE article_id = ?", (article_id,))
                    
                    # 删除相关的用户互动记录
                    cursor.execute("DELETE FROM user_article_interactions WHERE article_id = ?", (article_id,))
                    
                    # 删除文章
                    cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
                    
                    # 更新用户的文章计数
                    cursor.execute(
                        "UPDATE users SET posts_count = posts_count - 1 WHERE username = ?",
                        (author,)
                    )
                    
                    # 提交事务
                    conn.commit()
                    logger.info(f"成功删除文章及其相关数据: {article_id}")
                    return True
                else:
                    logger.warning(f"文章不存在: {article_id}")
                    return False
        except sqlite3.Error as e:
            logger.error(f"删除文章及其相关数据失败: {str(e)}")
            # 回滚事务
            conn.rollback()
            return False

    def add_complaint(self, article_id: int, reporter: str, reason: str) -> bool:
        """
        添加文章举报
        
        :param article_id: 文章ID
        :param reporter: 举报人用户名
        :param reason: 举报理由
        :return: 添加是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 检查文章是否存在
                cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
                if not cursor.fetchone():
                    logger.warning(f"文章不存在: {article_id}")
                    return False
                
                # 添加举报记录
                cursor.execute(
                    "INSERT INTO complaints (article_id, reporter, reason) VALUES (?, ?, ?)",
                    (article_id, reporter, reason)
                )
                
                # 增加文章的举报计数
                cursor.execute(
                    "UPDATE articles SET complain_count = complain_count + 1 WHERE id = ?",
                    (article_id,)
                )
                
                conn.commit()
                logger.info(f"成功添加举报: 文章 {article_id}，举报人: {reporter}")
                return True
        except sqlite3.Error as e:
            logger.error(f"添加举报失败: {str(e)}")
            return False

    def get_complained_articles(self) -> List[Dict[str, Any]]:
        """
        获取所有被举报的文章（用于重审）
        
        :return: 被举报的文章列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT a.id, a.title, a.author, a.created_at, a.complain_count 
                    FROM articles a 
                    WHERE a.complain_count > 0 AND a.status = 'approved'
                    ORDER BY a.complain_count DESC
                ''')
                articles = cursor.fetchall()
                return [dict(article) for article in articles]
        except sqlite3.Error as e:
            logger.error(f"获取被举报文章时发生错误: {str(e)}")
            return []

    def get_complaints_by_article(self, article_id: int) -> List[Dict[str, Any]]:
        """
        获取指定文章的所有举报
        
        :param article_id: 文章ID
        :return: 举报列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, reporter, reason, created_at FROM complaints WHERE article_id = ?",
                    (article_id,)
                )
                complaints = cursor.fetchall()
                return [dict(complaint) for complaint in complaints]
        except sqlite3.Error as e:
            logger.error(f"获取文章举报时发生错误: {str(e)}")
            return []

# 创建数据库实例
_db_instance = UserDatabase(settings.db_path)
# 保持原有的db变量名，确保兼容性
articles_db = _db_instance
# 添加这个别名，确保与其他模块保持一致
if 'db' not in locals():
    db = _db_instance

# 定义模块级便捷函数
def add_article(title: str, content: str, author: str) -> Optional[int]:
    return articles_db.add_article(title, content, author)


def get_article_by_id(article_id: int) -> Optional[Dict[str, Any]]:
    return db.get_article_by_id(article_id)


def get_pending_articles() -> List[Dict[str, Any]]:
    return db.get_pending_articles()


def update_article_status(article_id: int, status: str) -> bool:
    return db.update_article_status(article_id, status)


def search_articles(keyword: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    return db.search_articles(keyword, limit, offset)


def delete_article_and_related_data(article_id: int) -> bool:
    return db.delete_article_and_related_data(article_id)


def add_complaint(article_id: int, reporter: str, reason: str) -> bool:
    return db.add_complaint(article_id, reporter, reason)


def get_complained_articles() -> List[Dict[str, Any]]:
    return db.get_complained_articles()


def get_complaints_by_article(article_id: int) -> List[Dict[str, Any]]:
    return db.get_complaints_by_article(article_id)

# 定义__all__列表，指定可导出的对象
__all__ = [
    'db',
    'add_article',
    'get_article_by_id',
    'get_pending_articles',
    'update_article_status',
    'search_articles',
    'delete_article_and_related_data',
    'add_complaint',
    'get_complained_articles',
    'get_complaints_by_article'
]

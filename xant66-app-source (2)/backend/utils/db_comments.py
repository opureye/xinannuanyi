# 评论管理功能模块
import sqlite3
import logging
from datetime import datetime
from .db_core import UserDatabase as CoreUserDatabase  # 重命名为CoreUserDatabase以避免混淆
from backend.config import settings  # 添加settings导入

class UserDatabase(CoreUserDatabase):  # 修改为继承自CoreUserDatabase
    def add_comment(self, user_id, article_id, content):
        """添加新评论

        Args:
            user_id: 用户ID
            article_id: 文章ID
            content: 评论内容

        Returns:
            评论ID
        """
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO comments (user_id, article_id, content, created_at, status) VALUES (?, ?, ?, ?, ?)",
                    (user_id, article_id, content, current_time, 'pending')
                )
                comment_id = cursor.lastrowid
                conn.commit()
                return comment_id
        except sqlite3.Error as e:
            logging.error(f"添加评论失败: {e}")
            return None

    def get_comments_by_article(self, article_id):
        """根据文章ID获取所有已批准的评论

        Args:
            article_id: 文章ID

        Returns:
            评论列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT c.*, u.username FROM comments c JOIN users u ON c.user_id = u.id WHERE c.article_id = ? AND c.status = 'approved' ORDER BY c.created_at DESC",
                    (article_id,)
                )
                comments = cursor.fetchall()
                # 转换为字典列表
                return [{
                    'id': row[0],
                    'user_id': row[1],
                    'article_id': row[2],
                    'content': row[3],
                    'created_at': row[4],
                    'status': row[5],
                    'username': row[6]
                } for row in comments]
        except sqlite3.Error as e:
            logging.error(f"获取文章评论失败: {e}")
            return []

    def toggle_comment_like(self, user_id, comment_id):
        """点赞或取消点赞评论

        Args:
            user_id: 用户ID
            comment_id: 评论ID

        Returns:
            点赞状态 (True表示已点赞，False表示已取消点赞)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 检查是否已经点赞
                cursor.execute(
                    "SELECT id FROM user_comment_likes WHERE user_id = ? AND comment_id = ?",
                    (user_id, comment_id)
                )
                existing_like = cursor.fetchone()

                if existing_like:
                    # 取消点赞
                    cursor.execute(
                        "DELETE FROM user_comment_likes WHERE id = ?",
                        (existing_like[0],)
                    )
                    conn.commit()
                    return False
                else:
                    # 添加点赞
                    cursor.execute(
                        "INSERT INTO user_comment_likes (user_id, comment_id) VALUES (?, ?)",
                        (user_id, comment_id)
                    )
                    conn.commit()
                    return True
        except sqlite3.Error as e:
            logging.error(f"评论点赞操作失败: {e}")
            return None

    def get_comment_like_count(self, comment_id):
        """获取评论的点赞数量

        Args:
            comment_id: 评论ID

        Returns:
            点赞数量
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM user_comment_likes WHERE comment_id = ?",
                    (comment_id,)
                )
                count = cursor.fetchone()[0]
                return count
        except sqlite3.Error as e:
            logging.error(f"获取评论点赞数量失败: {e}")
            return 0

    def is_comment_liked_by_user(self, user_id, comment_id):
        """检查用户是否已点赞评论

        Args:
            user_id: 用户ID
            comment_id: 评论ID

        Returns:
            True if liked, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM user_comment_likes WHERE user_id = ? AND comment_id = ?",
                    (user_id, comment_id)
                )
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logging.error(f"检查评论点赞状态失败: {e}")
            return False

    def add_comment_complaint(self, user_id, comment_id, reason):
        """添加评论举报

        Args:
            user_id: 举报用户ID
            comment_id: 被举报评论ID
            reason: 举报原因

        Returns:
            举报ID
        """
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO comment_complaints (user_id, comment_id, reason, created_at, status) VALUES (?, ?, ?, ?, ?)",
                    (user_id, comment_id, reason, current_time, 'pending')
                )
                complaint_id = cursor.lastrowid
                conn.commit()
                # 更新评论状态为被举报
                cursor.execute(
                    "UPDATE comments SET status = 'complained' WHERE id = ?",
                    (comment_id,)
                )
                conn.commit()
                return complaint_id
        except sqlite3.Error as e:
            logging.error(f"添加评论举报失败: {e}")
            return None

    def get_complained_comments(self):
        """获取所有被举报的评论

        Returns:
            被举报评论列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT c.*, u.username FROM comments c JOIN users u ON c.user_id = u.id WHERE c.status = 'complained' ORDER BY c.created_at DESC"
                )
                comments = cursor.fetchall()
                # 转换为字典列表
                return [{
                    'id': row[0],
                    'user_id': row[1],
                    'article_id': row[2],
                    'content': row[3],
                    'created_at': row[4],
                    'status': row[5],
                    'username': row[6]
                } for row in comments]
        except sqlite3.Error as e:
            logging.error(f"获取被举报评论失败: {e}")
            return []

    def get_complaints_by_comment(self, comment_id):
        """获取指定评论的所有举报

        Args:
            comment_id: 评论ID

        Returns:
            举报列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT cc.*, u.username FROM comment_complaints cc JOIN users u ON cc.user_id = u.id WHERE cc.comment_id = ?",
                    (comment_id,)
                )
                complaints = cursor.fetchall()
                # 转换为字典列表
                return [{
                    'id': row[0],
                    'user_id': row[1],
                    'comment_id': row[2],
                    'reason': row[3],
                    'created_at': row[4],
                    'status': row[5],
                    'username': row[6]
                } for row in complaints]
        except sqlite3.Error as e:
            logging.error(f"获取评论举报失败: {e}")
            return []

    def update_comment_status(self, comment_id, status):
        """更新评论状态

        Args:
            comment_id: 评论ID
            status: 状态 (approved/rejected)

        Returns:
            是否更新成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE comments SET status = ? WHERE id = ?",
                    (status, comment_id)
                )
                conn.commit()

                # 如果状态为rejected，删除相关数据
                if status == 'rejected':
                    # 删除评论点赞
                    cursor.execute(
                        "DELETE FROM user_comment_likes WHERE comment_id = ?",
                        (comment_id,)
                    )
                    # 删除评论举报
                    cursor.execute(
                        "DELETE FROM comment_complaints WHERE comment_id = ?",
                        (comment_id,)
                    )
                    conn.commit()

                return True
        except sqlite3.Error as e:
            logging.error(f"更新评论状态失败: {e}")
            return False

# 创建数据库实例
_db_instance = UserDatabase(settings.db_path)  # 使用settings.db_path初始化
# 保持原有的comments_db变量名
comments_db = _db_instance
# 添加db别名，确保与其他模块保持一致
if 'db' not in locals():
    db = _db_instance

# 导出便捷函数
__all__ = [
    'UserDatabase',
    'CommentDatabase',
    'add_comment',
    'get_comments_by_article',
    'toggle_comment_like',
    'get_comment_like_count',
    'is_comment_liked_by_user',
    'add_comment_complaint',
    'get_complained_comments',
    'get_complaints_by_comment',
    'update_comment_status'
]

# 更新所有便捷函数以使用新的实例名

def add_comment(user_id, article_id, content):
    return comments_db.add_comment(user_id, article_id, content)

def get_comments_by_article(article_id):
    return comments_db.get_comments_by_article(article_id)

def toggle_comment_like(user_id, comment_id):
    return comments_db.toggle_comment_like(user_id, comment_id)

def get_comment_like_count(comment_id):
    return comments_db.get_comment_like_count(comment_id)

def is_comment_liked_by_user(user_id, comment_id):
    return comments_db.is_comment_liked_by_user(user_id, comment_id)

def add_comment_complaint(user_id, comment_id, reason):
    return comments_db.add_comment_complaint(user_id, comment_id, reason)

def get_complained_comments():
    return comments_db.get_complained_comments()

def get_complaints_by_comment(comment_id):
    return comments_db.get_complaints_by_comment(comment_id)

def update_comment_status(comment_id, status):
    return comments_db.update_comment_status(comment_id, status)

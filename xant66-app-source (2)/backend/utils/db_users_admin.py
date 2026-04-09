import sqlite3  # 添加sqlite3导入
from typing import Dict, Any, List

# 从core模块导入ExtendedUserDatabase基类
from .db_users_core import ExtendedUserDatabase, logger

def get_all_users(self, offset: int = 0, page_size: int = 20) -> List[Dict[str, Any]]:
    """
    获取所有用户信息（支持分页）
    
    :param offset: 偏移量
    :param page_size: 每页大小
    :return: 用户列表
    """
    try:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email, phone, created_at, role, status FROM users LIMIT ? OFFSET ?",
                (page_size, offset)
            )
            users = cursor.fetchall()
            
            # 转换为字典列表并处理字段名称
            result = []
            for user in users:
                user_dict = dict(user)
                # 确保字段名称和类型正确
                result.append({
                    "id": user_dict["id"],
                    "username": user_dict["username"],
                    "email": user_dict["email"],
                    "phone": str(user_dict.get("phone", "")) if "phone" in user_dict else "",  # 确保phone始终是字符串
                    "created_at": user_dict["created_at"],
                    "role": user_dict.get("role", "使用者"),
                    "is_admin": user_dict.get("role") == "管理员",
                    "is_banned": user_dict.get("status") == "banned"
                })
            
            return result
    except sqlite3.Error as e:
        logger.error(f"获取所有用户时发生错误: {str(e)}")
        return []

def get_total_users_count(self) -> int:
    """
    获取用户总数
    
    :return: 用户总数
    """
    try:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            return count
    except sqlite3.Error as e:
        logger.error(f"获取用户总数时发生错误: {str(e)}")
        return 0

def ban_user(self, user_id: int) -> bool:
    """
    封禁用户
    
    :param user_id: 用户ID
    :return: 操作是否成功
    """
    try:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET status = 'banned', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"封禁用户失败: {str(e)}")
        return False

def unban_user(self, user_id: int) -> bool:
    """
    解封用户
    
    :param user_id: 用户ID
    :return: 操作是否成功
    """
    try:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET status = 'active', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"解封用户失败: {str(e)}")
        return False

def delete_user(self, user_id: int) -> Dict[str, Any]:
    try:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取用户名
            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                return {"success": False, "message": "用户不存在"}
            username = user[0]
            
            # 删除用户的成就记录
            cursor.execute("DELETE FROM user_achievements WHERE user_id = ?", (user_id,))
            
            # 删除用户的关注记录 (作为粉丝) - 修复字段名
            cursor.execute("DELETE FROM follows WHERE follower = ?", (username,))
            
            # 删除用户的关注记录 (作为被关注者) - 修复字段名
            cursor.execute("DELETE FROM follows WHERE following = ?", (username,))
            
            # 删除用户的收藏记录
            cursor.execute("DELETE FROM collections WHERE user_id = ?", (user_id,))
            
            # 删除用户的评论
            cursor.execute("DELETE FROM comments WHERE user_id = ?", (user_id,))
            
            # 删除用户的文章 - 修复字段名
            cursor.execute("DELETE FROM articles WHERE author = ?", (username,))
            
            # 删除用户
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            conn.commit()
            logger.info(f"管理员删除用户成功: {username}")
            return {"success": True, "message": f"删除用户 {username} 成功"}
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        return {"success": False, "message": f"删除用户失败: {str(e)}"}

def search_users(self, username=None, email=None, is_banned=None, is_admin=None):
    """
    搜索用户
    
    :param username: 用户名搜索关键词
    :param email: 邮箱搜索关键词
    :param is_banned: 是否封禁
    :param is_admin: 是否管理员
    :return: 用户列表
    """
    try:
        # 修复：使用统一的数据库连接方式
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = "SELECT id, username, email, phone, created_at, role, status FROM users WHERE 1=1"
            params = []
            
            if username:
                query += " AND username LIKE ?"
                params.append(f"%{username}%")
            
            if email:
                query += " AND email LIKE ?"
                params.append(f"%{email}%")
            
            if is_banned is not None:
                query += " AND status = ?"
                params.append("banned" if is_banned else "active")
            
            if is_admin is not None:
                query += " AND role = ?"
                params.append("管理员")
            
            cursor.execute(query, params)
            users = cursor.fetchall()
            
            # 转换为字典列表并处理字段名称
            result = []
            for user in users:
                # 修复：如果返回的是元组而不是字典，需要手动构建字典
                if isinstance(user, tuple):
                    # 按照查询的字段顺序构建字典
                    user_dict = {
                        "id": user[0],
                        "username": user[1],
                        "email": user[2],
                        "phone": user[3] if len(user) > 3 else "",
                        "created_at": user[4] if len(user) > 4 else "",
                        "role": user[5] if len(user) > 5 else "使用者",
                        "status": user[6] if len(user) > 6 else "active"
                    }
                else:
                    user_dict = dict(user)
                
                result.append({
                    "user_id": user_dict["id"],
                    "username": user_dict["username"],
                    "email": user_dict["email"],
                    "phone": user_dict.get("phone", ""),
                    "created_at": user_dict["created_at"],
                    "role": user_dict.get("role", "使用者"),
                    "is_admin": user_dict.get("role") == "管理员",
                    "is_banned": user_dict.get("status") == "banned"
                })
            
            return result
    except sqlite3.Error as e:
        logger.error(f"搜索用户时发生错误: {str(e)}")
        return []

# 将方法绑定到ExtendedUserDatabase类
ExtendedUserDatabase.get_all_users = get_all_users
ExtendedUserDatabase.get_total_users_count = get_total_users_count
ExtendedUserDatabase.ban_user = ban_user
ExtendedUserDatabase.unban_user = unban_user
ExtendedUserDatabase.delete_user = delete_user
ExtendedUserDatabase.search_users = search_users
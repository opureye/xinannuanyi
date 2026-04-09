from typing import Dict, Any, Optional, Tuple
import sqlite3

# 从core模块导入ExtendedUserDatabase基类
from .db_users_core import ExtendedUserDatabase, logger

def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
    """
    根据用户ID获取用户信息
    
    :param user_id: 用户ID
    :return: 用户信息字典，如果用户不存在则为None
    """
    try:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
    except sqlite3.Error as e:
        logger.error(f"根据ID获取用户信息失败: {str(e)}")
        return None

def verify_user(self, username: str, password: str) -> Tuple[bool, str]:
    """
    验证用户身份

    :param username: 用户名
    :param password: 密码
    :return: (验证是否成功, 错误消息/空字符串)
    """
    try:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            
            if not result:
                # 修改日志记录，确保显示正确的模块名
                logger.warning(f"[db_users] 用户不存在: {username}")
                # 同时记录正在使用的数据库路径
                logger.info(f"[db_users] 当前使用的数据库路径: {self.db_path}")
                return False, "用户不存在"
            
            stored_password = result[0]
            logger.info(f"[db_users] 找到用户 {username} 的密码哈希，开始验证")
            # 记录密码哈希的前30个字符，帮助调试
            logger.info(f"[db_users] 密码哈希: {stored_password[:30]}...")
            # 修复参数顺序，应该是(provided_password, stored_hash)
            if self._check_password(password, stored_password):
                return True, ""
            else:
                return False, "密码错误"
    except sqlite3.Error as e:
        logger.error(f"[db_users] 验证用户时发生错误: {str(e)}")
        return False, f"数据库错误: {str(e)}"

def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
    """
    根据邮箱获取用户信息
    
    :param email: 用户邮箱
    :return: 用户信息字典，如果用户不存在则为None
    """
    try:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email, phone, avatar, bio, level, experience, posts_count, fans_count, likes_count, helpful_posts_count, created_at, updated_at, last_login, role, status FROM users WHERE email = ?",
                (email,)
            )
            user = cursor.fetchone()
            
            if user:
                user_dict = dict(user)
                # 确保角色字段存在，如果不存在则设置默认值
                if "role" not in user_dict or user_dict["role"] is None:
                    user_dict["role"] = "使用者"
                return user_dict
            
            return None
    except sqlite3.Error as e:
        logger.error(f"获取用户信息时发生错误: {str(e)}")
        return None

def add_user(self, username: str, password: str, email: Optional[str] = None, phone: Optional[str] = None, role: str = "使用者", real_name: Optional[str] = None, id_card: Optional[str] = None) -> Optional[int]:
    """
    添加新用户
    
    :param username: 用户名
    :param password: 密码
    :param email: 电子邮件（可选）
    :param phone: 电话号码（可选）
    :param role: 用户角色（可选，默认"使用者"）
    :return: 新创建用户的ID，如果失败则返回None
    """
    try:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                logger.warning(f"用户名已存在: {username}")
                return None
            
            # 检查邮箱是否已存在（如果提供了邮箱）
            if email:
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    logger.warning(f"邮箱已被使用: {email}")
                    return None
            
            # 检查电话号码是否已存在（如果提供了电话号码）
            if phone:
                cursor.execute("SELECT id FROM users WHERE phone = ?", (phone,))
                if cursor.fetchone():
                    logger.warning(f"电话号码已被使用: {phone}")
                    return None
            # 检查身份证是否已存在（如果提供了身份证号）
            if id_card:
                cursor.execute("SELECT id FROM users WHERE id_card = ?", (id_card,))
                if cursor.fetchone():
                    logger.warning(f"身份证号已被使用: {id_card}")
                    return None
            
            # 加密密码
            password_hash = self._hash_password(password)
            
            # 添加用户，包含实名信息（如有）
            columns = ["username", "password_hash", "email", "role"]
            values = [username, password_hash, email, role]
            if phone:
                columns.append("phone")
                values.append(phone)
            if real_name:
                columns.append("real_name")
                values.append(real_name)
            if id_card:
                columns.append("id_card")
                values.append(id_card)

            placeholders = ", ".join(["?" for _ in values])
            cursor.execute(
                f"INSERT INTO users ({', '.join(columns)}) VALUES ({placeholders})",
                tuple(values)
            )
            
            # 获取新创建用户的ID
            user_id = cursor.lastrowid
            conn.commit()
            logger.info(f"成功添加用户: {username}, 角色: {role}, 用户ID: {user_id}")
            return user_id
    except sqlite3.Error as e:
        logger.error(f"添加用户失败: {str(e)}")
        return None

def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
    """
    根据用户名获取用户信息
    
    :param username: 用户名
    :return: 用户信息字典，如果用户不存在则为None
    """
    try:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email, phone, avatar, bio, gender, birthday, level, experience, posts_count, fans_count, likes_count, helpful_posts_count, created_at, updated_at, last_login, role, status FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()
            
            if user:
                user_dict = dict(user)
                # 确保角色字段存在，如果不存在则设置默认值
                if "role" not in user_dict or user_dict["role"] is None:
                    user_dict["role"] = "使用者"
                    # 更新数据库中的角色信息
                    cursor.execute("UPDATE users SET role = ? WHERE username = ?", ("使用者", username))
                    conn.commit()
                # 添加is_banned字段，确保登录检查能正确工作
                user_dict["is_banned"] = user_dict.get("status") == "banned"
                # 添加is_admin字段，保持与其他方法一致
                user_dict["is_admin"] = user_dict.get("role") == "管理员"
                return user_dict
            
            return None
    except sqlite3.Error as e:
        logger.error(f"获取用户信息时发生错误: {str(e)}")
        return None

def get_user_count(self) -> int:
    
    try:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            return count
    except sqlite3.Error as e:
        logger.error(f"获取用户总数时发生错误: {str(e)}")
        return 0

def update_user_profile(self, username: str, profile_data: Dict[str, Any]) -> bool:
    """
    更新用户资料
    
    :param username: 用户名
    :param profile_data: 包含要更新的用户资料的字典
    :return: 更新是否成功
    """
    try:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if not cursor.fetchone():
                logger.warning(f"用户不存在: {username}")
                return False
            
            # 构建更新语句
            update_fields = []
            params = []
            
            if "avatar" in profile_data:
                update_fields.append("avatar = ?")
                params.append(profile_data["avatar"])
            
            if "bio" in profile_data:
                update_fields.append("bio = ?")
                params.append(profile_data["bio"])
            
            if "email" in profile_data:
                update_fields.append("email = ?")
                params.append(profile_data["email"])
            
            if "phone" in profile_data:
                update_fields.append("phone = ?")
                params.append(profile_data["phone"])

            if "gender" in profile_data:
                update_fields.append("gender = ?")
                params.append(profile_data["gender"])

            if "birthday" in profile_data:
                update_fields.append("birthday = ?")
                params.append(profile_data["birthday"])
            
            if not update_fields:
                # 没有需要更新的字段
                return True
            
            # 添加WHERE子句的参数
            params.append(username)
            
            # 执行更新
            cursor.execute(
                f"UPDATE users SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE username = ?",
                tuple(params)
            )
            
            conn.commit()
            logger.info(f"成功更新用户资料: {username}")
            return True
    except sqlite3.Error as e:
        logger.error(f"更新用户资料失败: {str(e)}")
        return False

def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
    """
    获取用户完整资料信息
    
    :param username: 用户名
    :return: 用户资料字典，如果用户不存在则为None
    """
    try:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, avatar, bio, level, experience, posts_count, fans_count, likes_count, helpful_posts_count FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()
            
            if user:
                return dict(user)
            
            return None
    except sqlite3.Error as e:
        logger.error(f"获取用户资料时发生错误: {str(e)}")
        return None

# 统一所有方法的数据库连接方式，将所有使用sqlite3.connect(self.db_path)的地方改为self._get_connection()

# 以下是其他方法的修复示例

def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
    """
    根据邮箱获取用户信息
    
    :param email: 用户邮箱
    :return: 用户信息字典，如果用户不存在则为None
    """
    try:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email, phone, avatar, bio, level, experience, posts_count, fans_count, likes_count, helpful_posts_count, created_at, updated_at, last_login, role, status FROM users WHERE email = ?",
                (email,)
            )
            user = cursor.fetchone()
            
            if user:
                user_dict = dict(user)
                # 确保角色字段存在，如果不存在则设置默认值
                if "role" not in user_dict or user_dict["role"] is None:
                    user_dict["role"] = "使用者"
                return user_dict
            
            return None
    except sqlite3.Error as e:
        logger.error(f"获取用户信息时发生错误: {str(e)}")
        return None

# 请类似地修改其他方法：add_user, get_user_by_username, get_user_count, update_user_profile, get_user_profile

def add_user(self, username: str, password: str, email: Optional[str] = None, phone: Optional[str] = None, role: str = "使用者", real_name: Optional[str] = None, id_card: Optional[str] = None) -> Optional[int]:
    """
    添加新用户
    
    :param username: 用户名
    :param password: 密码
    :param email: 电子邮件（可选）
    :param phone: 电话号码（可选）
    :param role: 用户角色（可选，默认"使用者"）
    :return: 新创建用户的ID，如果失败则返回None
    """
    try:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                logger.warning(f"用户名已存在: {username}")
                return None
            
            # 检查邮箱是否已存在（如果提供了邮箱）
            if email:
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    logger.warning(f"邮箱已被使用: {email}")
                    return None
            
            # 检查电话号码是否已存在（如果提供了电话号码）
            if phone:
                cursor.execute("SELECT id FROM users WHERE phone = ?", (phone,))
                if cursor.fetchone():
                    logger.warning(f"电话号码已被使用: {phone}")
                    return None
            # 检查身份证是否已存在（如果提供了身份证号）
            if id_card:
                cursor.execute("SELECT id FROM users WHERE id_card = ?", (id_card,))
                if cursor.fetchone():
                    logger.warning(f"身份证号已被使用: {id_card}")
                    return None
            
            # 加密密码
            password_hash = self._hash_password(password)
            
            # 添加用户，包含实名信息（如有）
            columns = ["username", "password_hash", "email", "role"]
            values = [username, password_hash, email, role]
            if phone:
                columns.append("phone")
                values.append(phone)
            if real_name:
                columns.append("real_name")
                values.append(real_name)
            if id_card:
                columns.append("id_card")
                values.append(id_card)

            placeholders = ", ".join(["?" for _ in values])
            cursor.execute(
                f"INSERT INTO users ({', '.join(columns)}) VALUES ({placeholders})",
                tuple(values)
            )
            
            # 获取新创建用户的ID
            user_id = cursor.lastrowid
            conn.commit()
            logger.info(f"成功添加用户: {username}, 角色: {role}, 用户ID: {user_id}")
            return user_id
    except sqlite3.Error as e:
        logger.error(f"添加用户失败: {str(e)}")
        return None

def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
    """
    根据用户名获取用户信息
    
    :param username: 用户名
    :return: 用户信息字典，如果用户不存在则为None
    """
    try:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email, phone, avatar, bio, level, experience, posts_count, fans_count, likes_count, helpful_posts_count, created_at, updated_at, last_login, role, status FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()
            
            if user:
                user_dict = dict(user)
                # 确保角色字段存在，如果不存在则设置默认值
                if "role" not in user_dict or user_dict["role"] is None:
                    user_dict["role"] = "使用者"
                    # 更新数据库中的角色信息
                    cursor.execute("UPDATE users SET role = ? WHERE username = ?", ("使用者", username))
                    conn.commit()
                # 添加is_banned字段，确保登录检查能正确工作
                user_dict["is_banned"] = user_dict.get("status") == "banned"
                # 添加is_admin字段，保持与其他方法一致
                user_dict["is_admin"] = user_dict.get("role") == "管理员"
                return user_dict
            
            return None
    except sqlite3.Error as e:
        logger.error(f"获取用户信息时发生错误: {str(e)}")
        return None

def get_user_count(self) -> int:
    
    try:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            return count
    except sqlite3.Error as e:
        logger.error(f"获取用户总数时发生错误: {str(e)}")
        return 0

def update_user_profile(self, username: str, profile_data: Dict[str, Any]) -> bool:
    """
    更新用户资料
    
    :param username: 用户名
    :param profile_data: 包含要更新的用户资料的字典
    :return: 更新是否成功
    """
    try:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if not cursor.fetchone():
                logger.warning(f"用户不存在: {username}")
                return False
            
            # 构建更新语句
            update_fields = []
            params = []
            
            if "avatar" in profile_data:
                update_fields.append("avatar = ?")
                params.append(profile_data["avatar"])
            
            if "bio" in profile_data:
                update_fields.append("bio = ?")
                params.append(profile_data["bio"])
            
            if "email" in profile_data:
                update_fields.append("email = ?")
                params.append(profile_data["email"])
            
            if "phone" in profile_data:
                update_fields.append("phone = ?")
                params.append(profile_data["phone"])
            
            if not update_fields:
                # 没有需要更新的字段
                return True
            
            # 添加WHERE子句的参数
            params.append(username)
            
            # 执行更新
            cursor.execute(
                f"UPDATE users SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE username = ?",
                tuple(params)
            )
            
            conn.commit()
            logger.info(f"成功更新用户资料: {username}")
            return True
    except sqlite3.Error as e:
        logger.error(f"更新用户资料失败: {str(e)}")
        return False

def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
    """
    获取用户完整资料信息
    
    :param username: 用户名
    :return: 用户资料字典，如果用户不存在则为None
    """
    try:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, avatar, bio, level, experience, posts_count, fans_count, likes_count, helpful_posts_count FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()
            
            if user:
                return dict(user)
            
            return None
    except sqlite3.Error as e:
        logger.error(f"获取用户资料时发生错误: {str(e)}")
        return None

# 将方法绑定到ExtendedUserDatabase类
ExtendedUserDatabase.get_user_by_id = get_user_by_id
ExtendedUserDatabase.verify_user = verify_user
ExtendedUserDatabase.get_user_by_email = get_user_by_email
ExtendedUserDatabase.add_user = add_user
ExtendedUserDatabase.get_user_by_username = get_user_by_username
ExtendedUserDatabase.get_user_count = get_user_count
ExtendedUserDatabase.update_user_profile = update_user_profile
ExtendedUserDatabase.get_user_profile = get_user_profile
# 导入所有子模块以确保方法已绑定到类
from .db_users_core import ExtendedUserDatabase
from .db_users_password import *
from .db_users_basic import *
from .db_users_relationships import *
from .db_users_achievements import *
from .db_users_admin import *

from backend.config import settings

# 创建数据库实例 - 这是类定义结束后的代码
# 使用配置中的路径
_db_instance = ExtendedUserDatabase(settings.db_path)
# 保持原有的db变量名，确保兼容性
users_db = _db_instance
# 添加这个别名，确保与其他模块保持一致
db = _db_instance

# 添加便捷函数
def get_user_post_count(user_id):
    return users_db.get_user_post_count(user_id)

def get_user_collection_count(user_id):
    return users_db.get_user_collection_count(user_id)

def get_user_followers_count(user_id):
    return users_db.get_user_followers_count(user_id)

def get_user_following_count(user_id):
    return users_db.get_user_following_count(user_id)

def verify_user(username, password):
    return users_db.verify_user(username, password)

def add_user(username, password, email=None, phone=None, role="使用者", real_name=None, id_card=None):
    return users_db.add_user(username, password, email, phone, role, real_name, id_card)

def get_user_by_username(username):
    return users_db.get_user_by_username(username)

def get_user_count():
    return users_db.get_user_count()

def update_user_profile(username, profile_data):
    return users_db.update_user_profile(username, profile_data)

def get_user_profile(username):
    return users_db.get_user_profile(username)

def get_user_achievements(user_id):
    return users_db.get_user_achievements(user_id)

def unlock_achievement(user_id, achievement_id):
    return users_db.unlock_achievement(user_id, achievement_id)

def add_achievement(title, description, icon='fa-trophy', condition='完成特定任务', points=0):
    return users_db.add_achievement(title, description, icon, condition, points)

def get_total_users_count():
    return users_db.get_total_users_count()

def ban_user(user_id):
    return users_db.ban_user(user_id)

def unban_user(user_id):
    return users_db.unban_user(user_id)

def search_users(username=None, email=None, is_banned=None, is_admin=None):
    return users_db.search_users(username, email, is_banned, is_admin)

def delete_user(user_id):
    return users_db.delete_user(user_id)

def get_user_by_id(user_id):
    return users_db.get_user_by_id(user_id)

def get_user_by_email(email):
    return users_db.get_user_by_email(email)

def get_all_users(offset=0, page_size=20):
    return users_db.get_all_users(offset, page_size)

# 更新导出列表
export_list = ['users_db', 'db', 'verify_user', 'add_user', 'get_user_by_username', 'get_user_count', 'update_user_profile', 
               'get_user_profile', 'get_user_achievements', 'unlock_achievement', 'add_achievement', 
               'get_all_users', 'get_total_users_count', 'ban_user', 'unban_user', 'search_users', 'delete_user',
               'get_user_post_count', 'get_user_collection_count', 'get_user_followers_count', 'get_user_following_count',
               'get_user_by_id', 'get_user_by_email']
__all__ = export_list

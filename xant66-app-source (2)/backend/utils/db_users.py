# 此文件是重构后的入口文件，负责导入所有功能并重新导出

# 导入所有工具函数和数据库实例
from .db_users_utils import *

# 确保导出所有必要的功能
export_list = ['users_db', 'db', 'verify_user', 'add_user', 'get_user_by_username', 'get_user_count', 'update_user_profile', 
               'get_user_profile', 'get_user_achievements', 'unlock_achievement', 'add_achievement', 
               'get_all_users', 'get_total_users_count', 'ban_user', 'unban_user', 'search_users', 'delete_user',
               'get_user_post_count', 'get_user_collection_count', 'get_user_followers_count', 'get_user_following_count',
               'get_user_by_id', 'get_user_by_email']
__all__ = export_list
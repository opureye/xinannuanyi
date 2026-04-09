import sqlite3
import logging
import datetime

# 从core模块导入ExtendedUserDatabase基类
from .db_users_core import ExtendedUserDatabase, logger

def get_user_achievements(self, user_id):
    """获取用户的所有成就

    Args:
        user_id: 用户ID

    Returns:
        成就列表
    """
    try:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT a.*, ua.unlocked_at FROM achievements a LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = ?",
                (user_id,)
            )
            achievements = cursor.fetchall()
            return [{
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'icon': row[3],
                'condition': row[4],
                'points': row[5],
                'unlocked': row[6] is not None,
                'unlockedAt': row[6]
            } for row in achievements]
    except sqlite3.Error as e:
        logging.error(f"获取用户成就失败: {e}")
        return []

def unlock_achievement(self, user_id, achievement_id):
    """解锁用户成就

    Args:
        user_id: 用户ID
        achievement_id: 成就ID

    Returns:
        是否解锁成功
    """
    try:
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO user_achievements (user_id, achievement_id, unlocked_at) VALUES (?, ?, ?)",
                (user_id, achievement_id, current_time)
            )
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logging.error(f"解锁成就失败: {e}")
        return False

def add_achievement(self, title, description, icon='fa-trophy', condition='完成特定任务', points=0):
    """添加新成就

    Args:
        title: 成就标题
        description: 成就描述
        icon: 成就图标
        condition: 解锁条件
        points: 成就点数

    Returns:
        成就ID
    """
    try:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO achievements (title, description, icon, condition, points) VALUES (?, ?, ?, ?, ?)",
                (title, description, icon, condition, points)
            )
            achievement_id = cursor.lastrowid
            conn.commit()
            return achievement_id
    except sqlite3.Error as e:
        logging.error(f"添加成就失败: {e}")
        return None

# 将方法绑定到ExtendedUserDatabase类
ExtendedUserDatabase.get_user_achievements = get_user_achievements
ExtendedUserDatabase.unlock_achievement = unlock_achievement
ExtendedUserDatabase.add_achievement = add_achievement
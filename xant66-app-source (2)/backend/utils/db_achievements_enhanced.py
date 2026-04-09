"""
增强的成就系统模块
提供更多成就类型和自动解锁机制
"""
import sqlite3
import logging
import datetime
from typing import List, Dict, Any, Optional
from .sql_security import SQLSecurityValidator
from .db_locker import DatabaseLock

logger = logging.getLogger(__name__)


class AchievementManager:
    """成就管理器"""
    
    # 预定义成就列表
    DEFAULT_ACHIEVEMENTS = [
        # 发帖相关成就
        {"title": "初出茅庐", "description": "发布第一篇文章", "icon": "fa-feather-alt", "condition": "posts_count >= 1", "points": 10, "category": "content"},
        {"title": "文思泉涌", "description": "发布10篇文章", "icon": "fa-book", "condition": "posts_count >= 10", "points": 50, "category": "content"},
        {"title": "笔耕不辍", "description": "发布50篇文章", "icon": "fa-pen-fancy", "condition": "posts_count >= 50", "points": 200, "category": "content"},
        {"title": "著作等身", "description": "发布100篇文章", "icon": "fa-scroll", "condition": "posts_count >= 100", "points": 500, "category": "content"},
        
        # 点赞相关成就
        {"title": "初获青睐", "description": "文章获得第一个点赞", "icon": "fa-heart", "condition": "likes_count >= 1", "points": 10, "category": "social"},
        {"title": "备受喜爱", "description": "文章获得10个点赞", "icon": "fa-heartbeat", "condition": "likes_count >= 10", "points": 50, "category": "social"},
        {"title": "人气爆棚", "description": "文章获得100个点赞", "icon": "fa-fire", "condition": "likes_count >= 100", "points": 300, "category": "social"},
        {"title": "万人追捧", "description": "文章获得1000个点赞", "icon": "fa-crown", "condition": "likes_count >= 1000", "points": 1000, "category": "social"},
        
        # 粉丝相关成就
        {"title": "小有名气", "description": "拥有第一个粉丝", "icon": "fa-user-plus", "condition": "fans_count >= 1", "points": 20, "category": "social"},
        {"title": "初具规模", "description": "拥有10个粉丝", "icon": "fa-users", "condition": "fans_count >= 10", "points": 100, "category": "social"},
        {"title": "声名鹊起", "description": "拥有50个粉丝", "icon": "fa-user-friends", "condition": "fans_count >= 50", "points": 300, "category": "social"},
        {"title": "大V认证", "description": "拥有100个粉丝", "icon": "fa-star", "condition": "fans_count >= 100", "points": 500, "category": "social"},
        
        # 等级相关成就
        {"title": "初窥门径", "description": "达到5级", "icon": "fa-level-up-alt", "condition": "level >= 5", "points": 50, "category": "level"},
        {"title": "登堂入室", "description": "达到10级", "icon": "fa-mountain", "condition": "level >= 10", "points": 150, "category": "level"},
        {"title": "炉火纯青", "description": "达到20级", "icon": "fa-trophy", "condition": "level >= 20", "points": 400, "category": "level"},
        {"title": "登峰造极", "description": "达到30级", "icon": "fa-medal", "condition": "level >= 30", "points": 800, "category": "level"},
        
        # 评论相关成就
        {"title": "初次发言", "description": "发表第一条评论", "icon": "fa-comment", "condition": "comments_count >= 1", "points": 10, "category": "content"},
        {"title": "积极互动", "description": "发表10条评论", "icon": "fa-comments", "condition": "comments_count >= 10", "points": 50, "category": "content"},
        {"title": "评论达人", "description": "发表50条评论", "icon": "fa-comment-dots", "condition": "comments_count >= 50", "points": 200, "category": "content"},
        
        # 收藏相关成就
        {"title": "收藏家", "description": "收藏10篇文章", "icon": "fa-bookmark", "condition": "collections_count >= 10", "points": 50, "category": "content"},
        {"title": "收藏大师", "description": "收藏50篇文章", "icon": "fa-bookmark", "condition": "collections_count >= 50", "points": 200, "category": "content"},
        
        # 实用文章成就
        {"title": "实用专家", "description": "发布5篇实用文章", "icon": "fa-lightbulb", "condition": "helpful_posts_count >= 5", "points": 100, "category": "content"},
        {"title": "知识分享者", "description": "发布20篇实用文章", "icon": "fa-graduation-cap", "condition": "helpful_posts_count >= 20", "points": 300, "category": "content"},
        
        # 特殊成就
        {"title": "新手上路", "description": "注册账号", "icon": "fa-user-circle", "condition": "created_at IS NOT NULL", "points": 5, "category": "special"},
        {"title": "每日签到", "description": "连续登录7天", "icon": "fa-calendar-check", "condition": "login_streak >= 7", "points": 100, "category": "special"},
    ]
    
    def __init__(self, db_connection_getter):
        """
        初始化成就管理器
        
        Args:
            db_connection_getter: 获取数据库连接的方法或连接对象
        """
        self.get_connection = db_connection_getter
        self.lock_manager = DatabaseLock()
        self._initialize_achievements()
    
    def _get_raw_connection(self):
        """获取原始数据库连接（非上下文管理器）"""
        # get_connection应该是一个函数，返回一个sqlite3.Connection对象
        if callable(self.get_connection):
            conn = self.get_connection()
            return conn
        # 如果get_connection是连接对象本身（不应该发生）
        return self.get_connection
    
    def _initialize_achievements(self):
        """初始化默认成就"""
        try:
            conn = self._get_raw_connection()
            try:
                cursor = conn.cursor()
                
                # 检查是否已有成就
                cursor.execute("SELECT COUNT(*) FROM achievements")
                count = cursor.fetchone()[0]
                
                if count == 0:
                    # 插入默认成就
                    for achievement in self.DEFAULT_ACHIEVEMENTS:
                        cursor.execute("""
                            INSERT INTO achievements (title, description, icon, condition, points, category)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            achievement['title'],
                            achievement['description'],
                            achievement['icon'],
                            achievement['condition'],
                            achievement['points'],
                            achievement.get('category', 'general')
                        ))
                    conn.commit()
                    logger.info(f"已初始化{len(self.DEFAULT_ACHIEVEMENTS)}个默认成就")
            finally:
                if conn:
                    conn.close()
        except sqlite3.Error as e:
            logger.error(f"初始化成就失败: {e}")
    
    
    def check_and_unlock_achievements(self, user_id: int) -> List[Dict[str, Any]]:
        """
        检查并解锁用户应得的成就
        
        Args:
            user_id: 用户ID
            
        Returns:
            新解锁的成就列表
        """
        unlocked_achievements = []
        
        try:
            with self.lock_manager.write_lock("achievements", timeout=5.0):
                with self.lock_manager.write_lock("user_achievements", timeout=5.0):
                    conn = self._get_raw_connection()
                    try:
                        conn.row_factory = sqlite3.Row
                        cursor = conn.cursor()
                        
                        # 获取用户信息
                        cursor.execute("""
                            SELECT id, username, posts_count, likes_count, fans_count, level,
                                   experience, helpful_posts_count, created_at
                            FROM users WHERE id = ?
                        """, (user_id,))
                        user = cursor.fetchone()
                        
                        if not user:
                            logger.warning(f"用户不存在: {user_id}")
                            return unlocked_achievements
                        
                        user_dict = dict(user)
                        
                        # 获取用户评论数
                        cursor.execute("SELECT COUNT(*) FROM comments WHERE user_id = ?", (user_id,))
                        comments_count = cursor.fetchone()[0]
                        user_dict['comments_count'] = comments_count
                        
                        # 获取用户收藏数
                        cursor.execute("SELECT COUNT(*) FROM collections WHERE user_id = ?", (user_id,))
                        collections_count = cursor.fetchone()[0]
                        user_dict['collections_count'] = collections_count
                        
                        # 获取用户已解锁的成就ID
                        cursor.execute("SELECT achievement_id FROM user_achievements WHERE user_id = ?", (user_id,))
                        unlocked_ids = {row[0] for row in cursor.fetchall()}
                        
                        # 获取所有成就
                        cursor.execute("SELECT * FROM achievements")
                        all_achievements = cursor.fetchall()
                        
                        # 检查每个成就
                        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        for achievement in all_achievements:
                            achievement_id = achievement['id']
                            
                            # 如果已解锁，跳过
                            if achievement_id in unlocked_ids:
                                continue
                            
                            # 评估成就条件
                            if self._evaluate_condition(achievement['condition'], user_dict):
                                # 解锁成就
                                cursor.execute("""
                                    INSERT OR IGNORE INTO user_achievements (user_id, achievement_id, unlocked_at)
                                    VALUES (?, ?, ?)
                                """, (user_id, achievement_id, current_time))
                                
                                unlocked_achievements.append({
                                    'id': achievement_id,
                                    'title': achievement['title'],
                                    'description': achievement['description'],
                                    'icon': achievement['icon'],
                                    'points': achievement['points'],
                                    'unlocked_at': current_time
                                })
                                
                                logger.info(f"用户{user_id}解锁成就: {achievement['title']}")
                        
                        conn.commit()
                    finally:
                        if conn:
                            conn.close()
                        
        except Exception as e:
            logger.error(f"检查和解锁成就失败: {e}", exc_info=True)
        
        return unlocked_achievements
    
    def _evaluate_condition(self, condition: str, user_data: Dict[str, Any]) -> bool:
        """
        评估成就条件（安全的条件解析）
        
        Args:
            condition: 条件字符串（例如: "posts_count >= 10"）
            user_data: 用户数据字典
            
        Returns:
            是否满足条件
        """
        try:
            # 使用简单的条件解析（避免使用eval）
            # 支持的格式：字段名 操作符 值
            # 操作符：>=, <=, >, <, =, ==, !=
            
            # 解析条件
            import re
            
            # 匹配模式：字段名 操作符 值
            pattern = r'(\w+)\s*(>=|<=|>|<|==|=|!=)\s*(.+)'
            match = re.match(pattern, condition.strip())
            
            if not match:
                # 如果无法解析，尝试简单匹配
                if "IS NOT NULL" in condition.upper():
                    field = condition.split()[0].strip()
                    value = user_data.get(field)
                    return value is not None
                return False
            
            field_name = match.group(1)
            operator = match.group(2)
            value_str = match.group(3).strip()
            
            # 获取字段值
            field_value = user_data.get(field_name)
            if field_value is None:
                return False
            
            # 解析比较值
            try:
                if value_str.replace('.', '').replace('-', '').isdigit():
                    compare_value = float(value_str)
                    field_value = float(field_value)
                else:
                    compare_value = value_str.strip('"\'')
            except ValueError:
                compare_value = value_str.strip('"\'').lower()
                field_value = str(field_value).lower()
            
            # 执行比较
            if operator == '>=':
                return field_value >= compare_value
            elif operator == '<=':
                return field_value <= compare_value
            elif operator == '>':
                return field_value > compare_value
            elif operator == '<':
                return field_value < compare_value
            elif operator in ['=', '==']:
                return field_value == compare_value
            elif operator == '!=':
                return field_value != compare_value
            else:
                logger.warning(f"不支持的操作符: {operator}")
                return False
                
        except Exception as e:
            logger.error(f"评估条件失败: {condition} - {e}")
            return False
    
    def get_user_achievements(self, user_id: int, include_user_info: bool = False) -> List[Dict[str, Any]]:
        """
        获取用户的所有成就（包括已解锁和未解锁）
        
        Args:
            user_id: 用户ID
            include_user_info: 是否包含用户信息
            
        Returns:
            成就列表
        """
        try:
            conn = self._get_raw_connection()
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if include_user_info:
                    cursor.execute("""
                        SELECT a.*, ua.unlocked_at,
                               CASE WHEN ua.unlocked_at IS NOT NULL THEN 1 ELSE 0 END as unlocked,
                               u.username, u.avatar, u.level, u.experience
                        FROM achievements a
                        LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = ?
                        LEFT JOIN users u ON ua.user_id = u.id
                        ORDER BY unlocked DESC, a.points DESC
                    """, (user_id,))
                else:
                    cursor.execute("""
                        SELECT a.*, ua.unlocked_at,
                               CASE WHEN ua.unlocked_at IS NOT NULL THEN 1 ELSE 0 END as unlocked
                        FROM achievements a
                        LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = ?
                        ORDER BY unlocked DESC, a.points DESC
                    """, (user_id,))
                
                achievements = cursor.fetchall()
                return [dict(ach) for ach in achievements]
            finally:
                if conn:
                    conn.close()
        except sqlite3.Error as e:
            logger.error(f"获取用户成就失败: {e}")
            return []
    
    def get_user_achievement_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户成就统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息字典
        """
        try:
            conn = self._get_raw_connection()
            try:
                cursor = conn.cursor()
                
                # 获取总成就数
                cursor.execute("SELECT COUNT(*) FROM achievements")
                total_achievements = cursor.fetchone()[0]
                
                # 获取用户已解锁成就数
                cursor.execute("SELECT COUNT(*) FROM user_achievements WHERE user_id = ?", (user_id,))
                unlocked_count = cursor.fetchone()[0]
                
                # 获取用户总成就点数
                cursor.execute("""
                    SELECT COALESCE(SUM(a.points), 0) 
                    FROM user_achievements ua
                    JOIN achievements a ON ua.achievement_id = a.id
                    WHERE ua.user_id = ?
                """, (user_id,))
                total_points = cursor.fetchone()[0]
                
                # 按分类统计
                cursor.execute("""
                    SELECT a.category, COUNT(*) as count
                    FROM user_achievements ua
                    JOIN achievements a ON ua.achievement_id = a.id
                    WHERE ua.user_id = ?
                    GROUP BY a.category
                """, (user_id,))
                category_stats = {row[0]: row[1] for row in cursor.fetchall()}
                
                return {
                    'total_achievements': total_achievements,
                    'unlocked_count': unlocked_count,
                    'locked_count': total_achievements - unlocked_count,
                    'unlock_percentage': round((unlocked_count / total_achievements * 100) if total_achievements > 0 else 0, 2),
                    'total_points': total_points,
                    'category_statistics': category_stats
                }
            finally:
                if conn:
                    conn.close()
        except sqlite3.Error as e:
            logger.error(f"获取用户成就统计失败: {e}")
            return {
                'total_achievements': 0,
                'unlocked_count': 0,
                'locked_count': 0,
                'unlock_percentage': 0,
                'total_points': 0,
                'category_statistics': {}
            }
    
    def get_all_users_achievement_statistics(self) -> List[Dict[str, Any]]:
        """
        获取所有用户的成就统计信息
        
        Returns:
            所有用户的成就统计列表
        """
        try:
            conn = self._get_raw_connection()
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 获取总成就数
                cursor.execute("SELECT COUNT(*) FROM achievements")
                total_achievements = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT u.id as user_id, u.username, u.avatar, u.level, u.experience,
                           COUNT(ua.achievement_id) as unlocked_count,
                           COALESCE(SUM(a.points), 0) as total_points,
                           CASE WHEN ? > 0 THEN 
                               ROUND((COUNT(ua.achievement_id) / ? * 100), 2)
                           ELSE 0 END as unlock_percentage
                    FROM users u
                    LEFT JOIN user_achievements ua ON u.id = ua.user_id
                    LEFT JOIN achievements a ON ua.achievement_id = a.id
                    GROUP BY u.id
                    ORDER BY total_points DESC, unlocked_count DESC
                """, (total_achievements, total_achievements))
                
                users_stats = cursor.fetchall()
                return [dict(stat) for stat in users_stats]
            finally:
                if conn:
                    conn.close()
        except sqlite3.Error as e:
            logger.error(f"获取所有用户成就统计失败: {e}")
            return []
    
    def get_achievement_unlocked_users(self, achievement_id: int) -> Dict[str, Any]:
        """
        获取解锁特定成就的用户列表
        
        Args:
            achievement_id: 成就ID
            
        Returns:
            包含成就信息和解锁用户列表的字典
        """
        try:
            conn = self._get_raw_connection()
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 获取成就信息
                cursor.execute("SELECT * FROM achievements WHERE id = ?", (achievement_id,))
                achievement = cursor.fetchone()
                
                if not achievement:
                    return {}
                
                # 获取解锁该成就的用户列表
                cursor.execute("""
                    SELECT u.id as user_id, u.username, u.avatar, u.level, u.experience,
                           ua.unlocked_at
                    FROM users u
                    JOIN user_achievements ua ON u.id = ua.user_id
                    WHERE ua.achievement_id = ?
                    ORDER BY ua.unlocked_at DESC
                """, (achievement_id,))
                
                unlocked_users = cursor.fetchall()
                
                return {
                    'achievement': dict(achievement),
                    'unlocked_users_count': len(unlocked_users),
                    'unlocked_users': [dict(user) for user in unlocked_users]
                }
            finally:
                if conn:
                    conn.close()
        except sqlite3.Error as e:
            logger.error(f"获取成就解锁用户列表失败: {e}")
            return {}
    
    def get_user_achievement_rankings(self, sort_by: str = 'points', limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取用户成就排名
        
        Args:
            sort_by: 排序方式，可选值：'points'（按成就点数）或 'count'（按解锁成就数量）
            limit: 返回结果数量限制
            
        Returns:
            用户成就排名列表
        """
        try:
            conn = self._get_raw_connection()
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 选择排序字段
                if sort_by == 'count':
                    sort_field = 'unlocked_count DESC'
                else:
                    sort_field = 'total_points DESC'
                
                cursor.execute(f"""
                    SELECT u.id as user_id, u.username, u.avatar, u.level, u.experience,
                           COUNT(ua.achievement_id) as unlocked_count,
                           COALESCE(SUM(a.points), 0) as total_points
                    FROM users u
                    LEFT JOIN user_achievements ua ON u.id = ua.user_id
                    LEFT JOIN achievements a ON ua.achievement_id = a.id
                    GROUP BY u.id
                    ORDER BY {sort_field}, u.id
                    LIMIT ?
                """, (limit,))
                
                rankings = cursor.fetchall()
                
                # 添加排名字段
                ranked_result = []
                for i, ranking in enumerate(rankings, 1):
                    ranking_dict = dict(ranking)
                    ranking_dict['rank'] = i
                    ranked_result.append(ranking_dict)
                
                return ranked_result
            finally:
                if conn:
                    conn.close()
        except sqlite3.Error as e:
            logger.error(f"获取用户成就排名失败: {e}")
            return []


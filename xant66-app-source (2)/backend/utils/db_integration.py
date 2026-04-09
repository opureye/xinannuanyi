"""
数据库功能集成模块
整合SQL注入防护、连接池、锁机制、跨表查询和成就系统
"""
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


def initialize_database_features(db_instance, enable_pool: bool = True, pool_size: int = 5):
    """
    初始化数据库的所有增强功能
    
    Args:
        db_instance: 数据库实例
        enable_pool: 是否启用连接池
        pool_size: 连接池大小
    """
    try:
        # 启用连接池
        if enable_pool:
            db_instance.enable_connection_pool(pool_size)
            logger.info("数据库连接池已启用")
        
        # 导入并初始化成就管理器
        try:
            from .db_achievements_enhanced import AchievementManager
            # 创建一个函数来获取原始连接（不使用上下文管理器）
            def get_raw_connection():
                import sqlite3
                conn = sqlite3.connect(db_instance.db_path, timeout=5.0)
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")
                return conn
            
            db_instance.achievement_manager = AchievementManager(get_raw_connection)
            logger.info("成就管理器已初始化")
        except Exception as e:
            logger.warning(f"初始化成就管理器失败: {e}")
        
        logger.info("数据库功能集成完成")
    except Exception as e:
        logger.error(f"数据库功能集成失败: {e}")


def get_safe_query_builder(connection):
    """
    获取安全的查询构建器
    
    Args:
        connection: 数据库连接
        
    Returns:
        JoinQueryBuilder实例
    """
    from .db_join_queries import JoinQueryBuilder
    return JoinQueryBuilder(connection)


def validate_input(value: Any, input_type: str = "string", **kwargs) -> tuple:
    """
    验证输入的统一接口
    
    Args:
        value: 要验证的值
        input_type: 输入类型（string, integer, table_name, column_name）
        **kwargs: 其他验证参数
        
    Returns:
        (是否有效, 错误信息)
    """
    from .sql_security import SQLSecurityValidator
    
    if input_type == "string":
        max_length = kwargs.get('max_length', 1000)
        return SQLSecurityValidator.validate_string(value, max_length)
    elif input_type == "integer":
        min_val = kwargs.get('min_val')
        max_val = kwargs.get('max_val')
        return SQLSecurityValidator.validate_integer(value, min_val, max_val)
    elif input_type == "table_name":
        return SQLSecurityValidator.validate_table_name(value)
    elif input_type == "column_name":
        return SQLSecurityValidator.validate_column_name(value)
    else:
        return False, f"未知的输入类型: {input_type}"


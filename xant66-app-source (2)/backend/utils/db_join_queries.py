-"""
跨表查询功能模块
提供安全的JOIN查询封装
"""
import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple
from .sql_security import SQLSecurityValidator, SafeQueryBuilder

logger = logging.getLogger(__name__)


class JoinQueryBuilder:
    """跨表查询构建器"""
    
    class JoinType:
        """JOIN类型"""
        INNER = "INNER JOIN"
        LEFT = "LEFT JOIN"
        RIGHT = "RIGHT JOIN"
        FULL = "FULL OUTER JOIN"
    
    def __init__(self, connection: sqlite3.Connection):
        """
        初始化查询构建器
        
        Args:
            connection: 数据库连接
        """
        self.conn = connection
        self.conn.row_factory = sqlite3.Row
    
    def join_tables(
        self,
        main_table: str,
        join_clauses: List[Tuple[str, str, str, str, str]],  # (表名, JOIN类型, 左表列, 右表列, 别名)
        select_columns: List[str] = None,
        where_conditions: List[Tuple[str, str, Any]] = None,
        order_by: List[Tuple[str, str]] = None,
        limit: int = None,
        offset: int = None
    ) -> List[Dict[str, Any]]:
        """
        执行多表JOIN查询
        
        Args:
            main_table: 主表名
            join_clauses: JOIN子句列表，每个元素为(表名, JOIN类型, 左表列, 右表列, 别名)
            select_columns: 要选择的列列表，格式如["users.username", "articles.title"]
            where_conditions: WHERE条件列表，每个元素为(列名, 操作符, 值)
            order_by: 排序列表，每个元素为(列名, ASC/DESC)
            limit: 限制返回行数
            offset: 偏移量
            
        Returns:
            查询结果列表
        """
        # 验证主表名
        is_valid, error = SQLSecurityValidator.validate_table_name(main_table)
        if not is_valid:
            raise ValueError(f"无效的主表名: {error}")
        
        # 构建SELECT子句
        if select_columns is None:
            select_clause = f"{main_table}.*"
        else:
            # 验证列名
            validated_columns = []
            for col in select_columns:
                if '.' in col:
                    table, column = col.split('.', 1)
                    is_valid_table, _ = SQLSecurityValidator.validate_table_name(table)
                    is_valid_col, _ = SQLSecurityValidator.validate_column_name(column)
                    if is_valid_table and is_valid_col:
                        validated_columns.append(col)
                    else:
                        logger.warning(f"跳过无效列: {col}")
                else:
                    is_valid, _ = SQLSecurityValidator.validate_column_name(col)
                    if is_valid:
                        validated_columns.append(f"{main_table}.{col}")
                    else:
                        logger.warning(f"跳过无效列: {col}")
            select_clause = ", ".join(validated_columns) if validated_columns else f"{main_table}.*"
        
        # 构建FROM和JOIN子句
        from_clause = main_table
        join_params = []
        
        for join_info in join_clauses:
            if len(join_info) < 4:
                raise ValueError("JOIN子句格式错误，至少需要4个元素：表名、JOIN类型、左表列、右表列")
            
            join_table = join_info[0]
            join_type = join_info[1] if len(join_info) > 1 else self.JoinType.INNER
            left_col = join_info[2] if len(join_info) > 2 else None
            right_col = join_info[3] if len(join_info) > 3 else None
            table_alias = join_info[4] if len(join_info) > 4 else join_table
            
            # 验证表名
            is_valid, error = SQLSecurityValidator.validate_table_name(join_table)
            if not is_valid:
                raise ValueError(f"无效的JOIN表名: {error}")
            
            # 验证列名
            if left_col:
                if '.' in left_col:
                    left_table, left_column = left_col.split('.', 1)
                    is_valid, _ = SQLSecurityValidator.validate_column_name(left_column)
                    if not is_valid:
                        raise ValueError(f"无效的左表列: {left_col}")
                else:
                    is_valid, _ = SQLSecurityValidator.validate_column_name(left_col)
                    if not is_valid:
                        raise ValueError(f"无效的左表列: {left_col}")
            
            if right_col:
                if '.' in right_col:
                    right_table, right_column = right_col.split('.', 1)
                    is_valid, _ = SQLSecurityValidator.validate_column_name(right_column)
                    if not is_valid:
                        raise ValueError(f"无效的右表列: {right_col}")
                else:
                    is_valid, _ = SQLSecurityValidator.validate_column_name(right_col)
                    if not is_valid:
                        raise ValueError(f"无效的右表列: {right_col}")
            
            if left_col and right_col:
                from_clause += f" {join_type} {join_table} AS {table_alias} ON {left_col} = {right_col}"
            else:
                logger.warning(f"JOIN条件不完整，跳过: {join_info}")
        
        # 构建WHERE子句
        where_clause = ""
        where_params = []
        if where_conditions:
            from .sql_security import SQLOperator
            # 转换条件格式
            sql_conditions = []
            for col, op, val in where_conditions:
                operator_map = {
                    '=': SQLOperator.EQUALS,
                    '!=': SQLOperator.NOT_EQUALS,
                    'LIKE': SQLOperator.LIKE,
                    '>': SQLOperator.GREATER_THAN,
                    '<': SQLOperator.LESS_THAN,
                    '>=': SQLOperator.GREATER_EQUAL,
                    '<=': SQLOperator.LESS_EQUAL,
                }
                operator = operator_map.get(op, SQLOperator.EQUALS)
                sql_conditions.append((col, operator, val))
            
            where_clause, where_params = SafeQueryBuilder.build_where_clause(sql_conditions)
            where_clause = "WHERE " + where_clause if where_clause else ""
        
        # 构建ORDER BY子句
        order_clause = ""
        if order_by:
            order_clause = SafeQueryBuilder.build_order_clause(order_by)
            order_clause = " " + order_clause if order_clause else ""
        
        # 构建LIMIT和OFFSET子句
        limit_clause = ""
        limit_params = []
        if limit is not None:
            limit_clause = " LIMIT ?"
            limit_params.append(limit)
            if offset is not None:
                limit_clause += " OFFSET ?"
                limit_params.append(offset)
        
        # 构建完整查询
        query = f"SELECT {select_clause} FROM {from_clause} {where_clause} {order_clause} {limit_clause}"
        
        try:
            cursor = self.conn.cursor()
            params = where_params + limit_params
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # 转换为字典列表
            return [dict(row) for row in results]
        except sqlite3.Error as e:
            logger.error(f"JOIN查询执行失败: {e}")
            raise
    
    def get_user_with_articles(
        self,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取用户及其文章（用户-文章JOIN查询示例）
        
        Args:
            user_id: 用户ID
            username: 用户名
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户和文章信息列表
        """
        join_clauses = [
            ("articles", self.JoinType.LEFT, "users.id", "articles.author_id", "a")
        ]
        
        select_columns = [
            "users.id", "users.username", "users.email", "users.avatar",
            "a.id AS article_id", "a.title", "a.content", "a.created_at AS article_created_at"
        ]
        
        where_conditions = []
        if user_id:
            where_conditions.append(("users.id", "=", user_id))
        if username:
            where_conditions.append(("users.username", "=", username))
        
        return self.join_tables(
            main_table="users",
            join_clauses=join_clauses,
            select_columns=select_columns,
            where_conditions=where_conditions,
            order_by=[("a.created_at", "DESC")],
            limit=limit,
            offset=offset
        )
    
    def get_article_with_comments(
        self,
        article_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取文章及其评论（文章-评论JOIN查询示例）
        
        Args:
            article_id: 文章ID
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            文章和评论信息列表
        """
        join_clauses = [
            ("comments", self.JoinType.LEFT, "articles.id", "comments.article_id", "c"),
            ("users", self.JoinType.LEFT, "c.user_id", "users.id", "u")
        ]
        
        select_columns = [
            "articles.id", "articles.title", "articles.content AS article_content",
            "articles.author", "articles.created_at AS article_created_at",
            "c.id AS comment_id", "c.content AS comment_content",
            "c.created_at AS comment_created_at",
            "u.username AS comment_author", "u.avatar AS comment_author_avatar"
        ]
        
        where_conditions = []
        if article_id:
            where_conditions.append(("articles.id", "=", article_id))
        
        return self.join_tables(
            main_table="articles",
            join_clauses=join_clauses,
            select_columns=select_columns,
            where_conditions=where_conditions,
            order_by=[("c.created_at", "ASC")],
            limit=limit,
            offset=offset
        )
    
    def get_user_achievements_with_details(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取用户成就详细信息（用户-成就关联-成就表JOIN查询示例）
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户成就列表
        """
        join_clauses = [
            ("user_achievements", self.JoinType.LEFT, "users.id", "user_achievements.user_id", "ua"),
            ("achievements", self.JoinType.LEFT, "ua.achievement_id", "achievements.id", "a")
        ]
        
        select_columns = [
            "users.id", "users.username",
            "a.id AS achievement_id", "a.title AS achievement_title",
            "a.description", "a.icon", "a.points",
            "ua.unlocked_at"
        ]
        
        where_conditions = [("users.id", "=", user_id)]
        
        return self.join_tables(
            main_table="users",
            join_clauses=join_clauses,
            select_columns=select_columns,
            where_conditions=where_conditions,
            order_by=[("ua.unlocked_at", "DESC")]
        )


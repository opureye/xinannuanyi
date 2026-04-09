"""
SQL注入防护工具模块
提供输入验证、清理和安全的SQL查询构建功能
"""
import re
import logging
from typing import Any, List, Optional, Union, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class SQLOperator(Enum):
    """SQL操作符枚举"""
    EQUALS = "="
    NOT_EQUALS = "!="
    LIKE = "LIKE"
    IN = "IN"
    BETWEEN = "BETWEEN"
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="


class SQLSecurityValidator:
    """SQL安全验证器"""
    
    # SQL关键字黑名单（用于检测潜在注入）
    SQL_KEYWORDS = {
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
        'EXEC', 'EXECUTE', 'UNION', 'SCRIPT', 'SCRIPT>', '--', '/*', '*/',
        'XP_', 'SP_', 'CHAR(', 'ASCII(', 'SUBSTRING(', 'CAST(', 'CONVERT('
    }
    
    # 危险的字符模式
    DANGEROUS_PATTERNS = [
        r';\s*(DROP|DELETE|UPDATE|INSERT|CREATE|ALTER)',  # 命令分隔符后跟危险命令
        r'--',  # SQL注释
        r'/\*.*?\*/',  # 多行注释
        r'UNION.*?SELECT',  # UNION注入
        r'XP_',  # 扩展存储过程
        r'EXEC\s*\(',  # 执行命令
        r'0x[0-9a-fA-F]+',  # 十六进制编码
    ]
    
    @staticmethod
    def validate_string(value: str, max_length: int = 1000, allow_special: bool = True) -> Tuple[bool, Optional[str]]:
        """
        验证字符串输入
        
        Args:
            value: 要验证的字符串
            max_length: 最大长度
            allow_special: 是否允许特殊字符
            
        Returns:
            (是否有效, 错误信息)
        """
        if not isinstance(value, str):
            return False, "输入必须是字符串类型"
        
        # 检查长度
        if len(value) > max_length:
            return False, f"输入长度超过最大限制({max_length}字符)"
        
        # 检查SQL关键字
        value_upper = value.upper().strip()
        for keyword in SQLSecurityValidator.SQL_KEYWORDS:
            if keyword in value_upper:
                # 允许在正常文本中使用这些词，但检查是否为独立的关键字
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, value_upper):
                    return False, f"输入包含不允许的SQL关键字: {keyword}"
        
        # 检查危险模式
        for pattern in SQLSecurityValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE | re.DOTALL):
                return False, "输入包含潜在的SQL注入代码"
        
        return True, None
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """
        清理字符串输入（移除危险字符）
        
        Args:
            value: 要清理的字符串
            max_length: 最大长度
            
        Returns:
            清理后的字符串
        """
        if not isinstance(value, str):
            value = str(value)
        
        # 移除空字符
        value = value.replace('\x00', '')
        
        # 截断过长内容
        if len(value) > max_length:
            value = value[:max_length]
            logger.warning(f"输入字符串被截断到{max_length}字符")
        
        return value
    
    @staticmethod
    def validate_integer(value: Any, min_val: Optional[int] = None, max_val: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        验证整数输入
        
        Args:
            value: 要验证的值
            min_val: 最小值
            max_val: 最大值
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            int_val = int(value)
        except (ValueError, TypeError):
            return False, "输入必须是整数"
        
        if min_val is not None and int_val < min_val:
            return False, f"输入值必须大于等于{min_val}"
        
        if max_val is not None and int_val > max_val:
            return False, f"输入值必须小于等于{max_val}"
        
        return True, None
    
    @staticmethod
    def validate_table_name(table_name: str) -> Tuple[bool, Optional[str]]:
        """
        验证表名（只允许字母、数字和下划线）
        
        Args:
            table_name: 表名
            
        Returns:
            (是否有效, 错误信息)
        """
        if not isinstance(table_name, str):
            return False, "表名必须是字符串"
        
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            return False, "表名只能包含字母、数字和下划线，且必须以字母或下划线开头"
        
        return True, None
    
    @staticmethod
    def validate_column_name(column_name: str) -> Tuple[bool, Optional[str]]:
        """
        验证列名（只允许字母、数字和下划线）
        
        Args:
            column_name: 列名
            
        Returns:
            (是否有效, 错误信息)
        """
        if not isinstance(column_name, str):
            return False, "列名必须是字符串"
        
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column_name):
            return False, "列名只能包含字母、数字和下划线，且必须以字母或下划线开头"
        
        return True, None


class SafeQueryBuilder:
    """安全查询构建器"""
    
    @staticmethod
    def build_where_clause(
        conditions: List[Tuple[str, SQLOperator, Any]],
        logical_op: str = "AND"
    ) -> Tuple[str, List[Any]]:
        """
        安全地构建WHERE子句
        
        Args:
            conditions: 条件列表，每个元素为(列名, 操作符, 值)
            logical_op: 逻辑运算符（AND或OR）
            
        Returns:
            (WHERE子句, 参数列表)
        """
        if logical_op.upper() not in ['AND', 'OR']:
            raise ValueError("逻辑运算符必须是AND或OR")
        
        if not conditions:
            return "", []
        
        where_parts = []
        params = []
        
        for column, operator, value in conditions:
            # 验证列名
            is_valid, error = SQLSecurityValidator.validate_column_name(column)
            if not is_valid:
                raise ValueError(f"无效的列名: {column} - {error}")
            
            # 根据操作符构建条件
            if operator == SQLOperator.IN:
                if not isinstance(value, (list, tuple)):
                    raise ValueError("IN操作符的值必须是列表或元组")
                placeholders = ','.join('?' * len(value))
                where_parts.append(f"{column} IN ({placeholders})")
                params.extend(value)
            elif operator == SQLOperator.LIKE:
                if isinstance(value, str):
                    # 清理LIKE值
                    sanitized = SQLSecurityValidator.sanitize_string(value)
                    where_parts.append(f"{column} LIKE ?")
                    params.append(sanitized)
                else:
                    raise ValueError("LIKE操作符的值必须是字符串")
            elif operator == SQLOperator.BETWEEN:
                if not isinstance(value, (list, tuple)) or len(value) != 2:
                    raise ValueError("BETWEEN操作符的值必须是包含两个元素的列表或元组")
                where_parts.append(f"{column} BETWEEN ? AND ?")
                params.extend(value)
            else:
                # 其他操作符（=, !=, >, <, >=, <=）
                where_parts.append(f"{column} {operator.value} ?")
                params.append(value)
        
        where_clause = f" {logical_op} ".join(where_parts)
        return where_clause, params
    
    @staticmethod
    def build_order_clause(columns: List[Tuple[str, str]]) -> str:
        """
        安全地构建ORDER BY子句
        
        Args:
            columns: 列列表，每个元素为(列名, 排序方向ASC/DESC)
            
        Returns:
            ORDER BY子句
        """
        order_parts = []
        
        for column, direction in columns:
            # 验证列名
            is_valid, error = SQLSecurityValidator.validate_column_name(column)
            if not is_valid:
                raise ValueError(f"无效的列名: {column} - {error}")
            
            # 验证排序方向
            direction = direction.upper()
            if direction not in ['ASC', 'DESC']:
                raise ValueError("排序方向必须是ASC或DESC")
            
            order_parts.append(f"{column} {direction}")
        
        if not order_parts:
            return ""
        
        return "ORDER BY " + ", ".join(order_parts)


def validate_search_input(search_term: str, max_length: int = 200) -> str:
    """
    验证和清理搜索输入
    
    Args:
        search_term: 搜索词
        max_length: 最大长度
        
    Returns:
        清理后的搜索词
    """
    if not search_term:
        return ""
    
    # 验证输入
    is_valid, error = SQLSecurityValidator.validate_string(search_term, max_length=max_length)
    if not is_valid:
        logger.warning(f"搜索输入验证失败: {error}")
        # 即使验证失败，也尝试清理而不是直接拒绝
        return SQLSecurityValidator.sanitize_string(search_term, max_length=max_length)
    
    return SQLSecurityValidator.sanitize_string(search_term, max_length=max_length)


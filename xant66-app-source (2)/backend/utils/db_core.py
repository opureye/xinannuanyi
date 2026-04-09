# 在文件顶部添加配置导入
import os
import json
import secrets
import logging
import sqlite3
from typing import Dict

# 尝试导入密码学库
CRYPTO_AVAILABLE = False

# 修复配置导入语句 - 使用与main.py一致的导入方式
from backend.config import settings

# 在文件级别直接尝试导入密码学库，而不是在类初始化中
logger = None

try:
    # 配置日志
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
except:
    # 如果日志配置失败，创建一个简单的logger
    import sys
    logger = type('Logger', (object,), {
        'info': lambda self, msg: print(f'INFO: {msg}', file=sys.stderr),
        'error': lambda self, msg: print(f'ERROR: {msg}', file=sys.stderr),
        'warning': lambda self, msg: print(f'WARNING: {msg}', file=sys.stderr)
    })()

# 在文件级别尝试导入密码学库
try:
    from cryptography.hazmat.primitives.asymmetric import dh
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import serialization
    
    # 标记密码学库可用
    CRYPTO_AVAILABLE = True
    logger.info("密码学库导入成功")
except ImportError as e:
    logger.warning(f"无法导入密码学库: {str(e)}. 请使用 'pip install cryptography' 命令安装")
    CRYPTO_AVAILABLE = False
except Exception as e:
    logger.error(f"初始化密码学参数时出错: {str(e)}")
    CRYPTO_AVAILABLE = False

# 定义GroupParameters类，用于DH密钥交换
class GroupParameters:
    def __init__(self):
        # 预设DH参数（实际应用中应使用更长更安全的参数）
        self.parameters = None
        
        if CRYPTO_AVAILABLE:
            try:
                self.parameters = dh.generate_parameters(generator=2, key_size=2048)
                logger.info("成功生成DH参数")
            except Exception as e:
                logger.warning(f"生成DH参数失败，但密码学库仍可用: {str(e)}")
        else:
            logger.warning("密码学库不可用，无法生成DH参数")

# 核心数据库类
class UserDatabase:
    def __init__(self, db_path: str = None):
        # 如果未提供db_path，则使用配置中的路径
        if db_path is None:
            db_path = settings.db_path
        
        # 确保使用绝对路径
        self.db_path = os.path.abspath(db_path)
        
        # 确保数据库目录存在
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"创建数据库目录: {db_dir}")
            
        # 初始化数据库
        self._init_db()
        
        # 加载或生成系统密钥
        self._load_or_generate_system_keys()

    def _load_or_generate_system_keys(self):
        """
        加载或生成系统密钥
        """
        # 直接使用settings.keys_path作为绝对路径
        keys_path = settings.keys_path
        
        # 确保密钥目录存在
        keys_dir = os.path.dirname(keys_path)
        if not os.path.exists(keys_dir):
            try:
                os.makedirs(keys_dir)
                logger.info(f"创建密钥目录: {keys_dir}")
            except PermissionError as e:
                logger.error(f"无法创建密钥目录: {keys_dir} - {str(e)}")
                raise RuntimeError(f"权限不足，无法创建密钥目录: {keys_dir}") from e
            except Exception as e:
                logger.error(f"创建密钥目录失败: {keys_dir} - {str(e)}")
                raise RuntimeError(f"创建密钥目录时发生错误: {keys_dir}") from e
        
        try:
            # 尝试加载现有密钥
            if os.path.exists(keys_path):
                try:
                    with open(keys_path, 'r') as f:
                        keys_data = json.load(f)
                        self.private_key = keys_data.get('private_key')
                        self.public_key = keys_data.get('public_key')
                    logger.info("系统密钥加载成功")
                except json.JSONDecodeError as e:
                    logger.error(f"系统密钥文件格式错误: {keys_path} - {str(e)}")
                    raise RuntimeError(f"系统密钥文件格式损坏: {keys_path}") from e
                except PermissionError as e:
                    logger.error(f"无法访问系统密钥文件: {keys_path} - {str(e)}")
                    raise RuntimeError(f"权限不足，无法访问系统密钥文件: {keys_path}") from e
            else:
                # 生成新的RSA密钥对
                logger.info("生成新的系统密钥")
                # 此处应包含生成RSA密钥对的代码
                # 并将生成的密钥保存到keys_path
                # 生成新的随机密钥（简化版本）
                self.private_key = secrets.token_hex(32)
                self.public_key = secrets.token_hex(32)
                
                # 保存密钥到文件
                with open(keys_path, 'w') as f:
                    json.dump({
                        'private_key': self.private_key,
                        'public_key': self.public_key
                    }, f)
                logger.info(f"系统密钥已生成并保存到: {keys_path}")
        except FileNotFoundError as e:
            logger.error(f"系统密钥文件未找到: {keys_path} - {str(e)}")
            raise RuntimeError(f"无法加载系统密钥文件: {keys_path}") from e
        except Exception as e:
            logger.error(f"加载或生成系统密钥失败: {str(e)}")
            raise RuntimeError(f"系统密钥处理失败: {str(e)}") from e
    
    # 在初始化数据库的方法中修改articles表结构
    def _init_db(self):
        """
        初始化数据库，创建必要的表结构
        """
        # 确保数据库文件所在目录存在
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir)
                logger.info(f"创建数据库目录: {db_dir}")
            except Exception as e:
                logger.error(f"创建数据库目录失败: {str(e)}")
                raise
        
        try:
            # 创建数据库连接并创建必要的表
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 创建用户表（基础表）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        email TEXT UNIQUE,
                        phone TEXT UNIQUE,
                        real_name TEXT,
                        id_card TEXT UNIQUE,
                        role TEXT DEFAULT 'user',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        status TEXT DEFAULT 'active',
                        avatar TEXT,
                        bio TEXT,
                        gender TEXT,
                        birthday TEXT,
                        level INTEGER DEFAULT 0,
                        experience INTEGER DEFAULT 0,
                        posts_count INTEGER DEFAULT 0,
                        fans_count INTEGER DEFAULT 0,
                        likes_count INTEGER DEFAULT 0,
                        helpful_posts_count INTEGER DEFAULT 0
                    )
                ''')
                
                # 检查并添加可能缺失的字段（针对已存在的表）
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT UNIQUE")
                    conn.commit()
                except sqlite3.OperationalError:
                    # 如果字段已存在，则忽略错误
                    pass
                
                # 迁移：添加实名列 real_name
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN real_name TEXT")
                    conn.commit()
                except sqlite3.OperationalError:
                    pass
                
                # 迁移：添加身份证列 id_card（SQLite不支持在ALTER中添加唯一约束，改用索引）
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN id_card TEXT")
                    conn.commit()
                except sqlite3.OperationalError:
                    # 列已存在时忽略
                    pass

                # 迁移：添加性别与出生日期
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN gender TEXT")
                    conn.commit()
                except sqlite3.OperationalError:
                    pass
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN birthday TEXT")
                    conn.commit()
                except sqlite3.OperationalError:
                    pass

                # 为已存在的users表创建唯一索引，确保id_card唯一（允许多个NULL）
                try:
                    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_id_card ON users(id_card)")
                    conn.commit()
                except sqlite3.OperationalError:
                    pass
                    
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN fans_count INTEGER DEFAULT 0")
                    conn.commit()
                except sqlite3.OperationalError:
                    # 如果字段已存在，则忽略错误
                    pass
                
                # 创建系统配置表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_config (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                ''')
                
                # 创建文章表 - 添加category字段
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        author TEXT NOT NULL,
                        category TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        view_count INTEGER DEFAULT 0,
                        like_count INTEGER DEFAULT 0,
                        complain_count INTEGER DEFAULT 0,
                        helpful_count INTEGER DEFAULT 0,
                        unhelpful_count INTEGER DEFAULT 0,
                        FOREIGN KEY (author) REFERENCES users (username)
                    )
                ''')

                # 为已存在的表添加category字段
                try:
                    cursor.execute("ALTER TABLE articles ADD COLUMN category TEXT DEFAULT ''")
                    conn.commit()
                except sqlite3.OperationalError:
                    # 如果字段已存在，则忽略错误
                    pass

                # 为已存在的表添加helpful_count和unhelpful_count字段
                try:
                    cursor.execute("ALTER TABLE articles ADD COLUMN helpful_count INTEGER DEFAULT 0")
                    conn.commit()
                except sqlite3.OperationalError:
                    pass

                try:
                    cursor.execute("ALTER TABLE articles ADD COLUMN unhelpful_count INTEGER DEFAULT 0")
                    conn.commit()
                except sqlite3.OperationalError:
                    pass
                
                # 创建评论表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS comments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        article_id INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        FOREIGN KEY (article_id) REFERENCES articles (id)
                    )
                ''')
                
                # 创建评论点赞表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_comment_likes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        comment_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        FOREIGN KEY (comment_id) REFERENCES comments (id),
                        UNIQUE (user_id, comment_id)
                    )
                ''')
                
                # 创建评论举报表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS comment_complaints (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        comment_id INTEGER NOT NULL,
                        reason TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        FOREIGN KEY (comment_id) REFERENCES comments (id)
                    )
                ''')
                
                # 创建文章举报表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS complaints (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        article_id INTEGER NOT NULL,
                        reporter TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (article_id) REFERENCES articles (id),
                        FOREIGN KEY (reporter) REFERENCES users (username)
                    )
                ''')
                
                # 创建关注表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS follows (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        follower TEXT NOT NULL,
                        following TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (follower) REFERENCES users (username),
                        FOREIGN KEY (following) REFERENCES users (username),
                        UNIQUE (follower, following)
                    )
                ''')
                
                # 创建收藏表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS collections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        article_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        FOREIGN KEY (article_id) REFERENCES articles (id),
                        UNIQUE (user_id, article_id)
                    )
                ''')
                
                # 添加成就表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS achievements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        icon TEXT NOT NULL,
                        condition TEXT NOT NULL,
                        points INTEGER DEFAULT 0,
                        category TEXT DEFAULT 'general'
                    )
                ''')
                
                # 为已存在的表添加category字段
                try:
                    cursor.execute("ALTER TABLE achievements ADD COLUMN category TEXT DEFAULT 'general'")
                    conn.commit()
                except sqlite3.OperationalError:
                    # 如果字段已存在，则忽略错误
                    pass
                
                # 添加用户成就关联表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_achievements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        achievement_id INTEGER NOT NULL,
                        unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        FOREIGN KEY (achievement_id) REFERENCES achievements (id),
                        UNIQUE (user_id, achievement_id)
                    )
                ''')
                conn.commit()
                logger.info(f"数据库初始化成功，文件路径: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise
            
    def _get_connection(self):
        """
        获取数据库连接（支持连接池）
        
        :return: 数据库连接对象
        """
        # 如果存在连接池，使用连接池
        if hasattr(self, '_connection_pool'):
            return self._connection_pool.get_connection()
        
        # 否则使用传统方式
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            # 启用外键约束
            conn.execute("PRAGMA foreign_keys = ON")
            # 设置WAL模式以提高并发性能
            conn.execute("PRAGMA journal_mode = WAL")
            # 设置同步模式为NORMAL
            conn.execute("PRAGMA synchronous = NORMAL")
            return conn
        except sqlite3.Error as e:
            logger.error(f"获取数据库连接失败: {str(e)}")
            raise
    
    def enable_connection_pool(self, pool_size: int = 5):
        """
        启用连接池
        
        Args:
            pool_size: 连接池大小
        """
        try:
            from .db_locker import DatabaseConnectionPool
            self._connection_pool = DatabaseConnectionPool(self.db_path, pool_size=pool_size)
            logger.info(f"已启用数据库连接池，大小: {pool_size}")
        except ImportError:
            logger.warning("无法导入连接池模块，使用传统连接方式")
        except Exception as e:
            logger.error(f"启用连接池失败: {e}")
    
    def disable_connection_pool(self):
        """禁用连接池"""
        if hasattr(self, '_connection_pool'):
            self._connection_pool.close_all()
            delattr(self, '_connection_pool')
            logger.info("已禁用数据库连接池")
    
    def _kdf(self, shared_secret: bytes, salt: bytes, info: bytes, length: int) -> bytes:
        """
        密钥派生函数
        """
        if CRYPTO_AVAILABLE:
            from cryptography.hazmat.primitives.kdf.hkdf import HKDF
            from cryptography.hazmat.primitives import hashes
            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=length,
                salt=salt,
                info=info,
            )
            return hkdf.derive(shared_secret)
        else:
            # 简化版本，使用SHA-256
            import hashlib
            key_material = shared_secret + salt + info
            return hashlib.sha256(key_material).digest()[:length]

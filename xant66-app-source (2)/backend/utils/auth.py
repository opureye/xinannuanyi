# utils/auth.py
import secrets
import json  # 添加json导入
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging
import hashlib  # 新增导入
import jwt  # 新增导入
import hmac
import base64
import time
from fastapi import HTTPException, Depends, status  # 添加status导入
from fastapi.security import HTTPBearer, OAuth2PasswordBearer  # 添加OAuth2PasswordBearer导入
from pydantic import BaseModel

from backend.config import settings

logger = logging.getLogger(__name__)

class SessionData(BaseModel):
    username: str
    role: str
    login_time: datetime
    expires_at: datetime

class SessionManager:
    """简单的会话管理器，使用内存存储会话"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
        self.security = HTTPBearer(auto_error=False)
    
    def create_session(self, username: str, role: str) -> str:
        """创建新的会话"""
        session_id = secrets.token_urlsafe(32)
        login_time = datetime.now()
        expires_at = login_time + timedelta(hours=24)  # 24小时过期
        
        self.sessions[session_id] = SessionData(
            username=username,
            role=role,
            login_time=login_time,
            expires_at=expires_at
        )
        
        logger.info(f"创建会话: {username} ({role})")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """获取会话数据"""
        session_data = self.sessions.get(session_id)
        
        if session_data and session_data.expires_at < datetime.now():
            # 会话已过期
            del self.sessions[session_id]
            return None
            
        return session_data
    
    def destroy_session(self, session_id: str) -> bool:
        """销毁会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"销毁会话: {session_id}")
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        expired_sessions = [
            sid for sid, data in self.sessions.items()
            if data.expires_at < datetime.now()
        ]
        for sid in expired_sessions:
            del self.sessions[sid]
        
        if expired_sessions:
            logger.info(f"清理 {len(expired_sessions)} 个过期会话")

# 创建全局会话管理器实例
session_manager = SessionManager()

# 新增函数: 验证JWT令牌
def verify_token(token: str) -> dict:
    """验证JWT令牌"""
    try:
        try:
            if hasattr(jwt, "decode"):
                payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
                return payload
        except Exception:
            pass
        return safe_jwt_decode(token, settings.jwt_secret_key)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="令牌已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的令牌")

# 新增函数: 获取密码哈希
def get_password_hash(password: str) -> str:
    """生成密码哈希值，优先使用高级加密方法"""
    try:
        # 尝试使用db_users中的高级加密方法
        from utils.db_users import users_db
        return users_db._hash_password(password)
    except ImportError as e:
        logger.warning(f"无法使用高级加密，使用备用哈希方法: {str(e)}")
    except Exception as e:
        logger.error(f"高级加密失败，使用备用哈希方法: {str(e)}")
    
    # 备用方案：使用带有盐的SHA-256哈希
    import secrets
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return json.dumps({
        "version": "fallback",
        "hash": hashed,
        "salt": salt
    })

# 新增函数: 验证密码
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配，优先使用db_users中的验证方法"""
    try:
        # 尝试使用db_users中的验证方法
        from utils.db_users import users_db
        return users_db._check_password(plain_password, hashed_password)
    except ImportError as e:
        logger.warning(f"无法使用高级验证，使用备用验证方法: {str(e)}")
    except Exception as e:
        logger.error(f"高级验证失败，使用备用验证方法: {str(e)}")
    
    # 备用方案：解析JSON并验证
    try:
        import json
        password_data = json.loads(hashed_password)
        if password_data.get("version") == "fallback":
            # 验证备用哈希
            hashed = hashlib.sha256((plain_password + password_data["salt"]).encode()).hexdigest()
            return hashed == password_data["hash"]
        elif password_data.get("version") == 1:
            # 验证版本1的哈希
            hashed = hashlib.sha256((plain_password + password_data["salt"]).encode()).hexdigest()
            return hashed == password_data["hash"]
    except:
        pass
    
    # 最简化的验证，仅作为最后的降级方案
    # 注意：这不安全，仅用于向后兼容
    return False

# 认证依赖项
def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/auth/token"))):
    """
    获取当前登录用户信息
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 尝试解码JWT令牌
        # 修复：使用正确的配置项jwt_secret_key，并为算法提供默认值'HS256'
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=['HS256'])
        except Exception:
            payload = safe_jwt_decode(token, settings.jwt_secret_key)
        username: str = payload.get("sub")
        
        if username is None:
            logger.warning("JWT令牌中未找到用户名")
            raise credentials_exception
            
        # 检查用户是否存在
        # 修复：使用统一的users_db实例
        from utils.db_users import users_db
        user = users_db.get_user_by_username(username)

        if user is None:
            logger.warning(f"JWT令牌中的用户不存在: {username}")
            raise credentials_exception

        if user.get("status") != "active":
            logger.warning(f"用户账户未激活: {username}")
            raise HTTPException(status_code=403, detail="用户账户未激活")
            
        # 创建SessionData对象
        session_data = SessionData(
            username=username,
            role=user.get("role", "user"),
            login_time=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        logger.info(f"用户认证成功: {username}, 角色: {user.get('role', 'user')}")
        return session_data
        
    # 修复：使用正确的异常类型PyJWTError替代不存在的JWTError
    except jwt.PyJWTError as e:
        logger.error(f"JWT令牌解码失败: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"用户认证过程中发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="认证过程中发生错误")
    
    session_id = credentials.credentials
    # 仅记录会话ID的前8个字符，保护安全
    logger.info(f"收到认证请求，会话ID: {session_id[:8]}...")
    
    session_data = session_manager.get_session(session_id)
    if not session_data:
        logger.warning(f"401错误: 会话无效或已过期，会话ID: {session_id[:8]}...")
        raise HTTPException(status_code=401, detail="会话无效或已过期")
    
    logger.info(f"认证成功: 用户 {session_data.username} (角色: {session_data.role})，会话ID: {session_id[:8]}...")
    return session_data

# 可选的用户认证函数
def get_current_user_optional(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False))):
    """
    获取当前登录用户信息（可选，不会抛出异常）
    """
    if not token:
        return None
        
    try:
        # 尝试解码JWT令牌
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=['HS256'])
        username: str = payload.get("sub")
        
        if username is None:
            return None
            
        # 检查用户是否存在
        from utils.db_users import users_db
        user = users_db.get_user_by_username(username)

        if user is None or user.get("status") != "active":
            return None
            
        # 创建SessionData对象
        session_data = SessionData(
            username=username,
            role=user.get("role", "user"),
            login_time=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        return session_data
        
    except Exception:
        return None

# 角色检查依赖项
def require_role(required_role: str):
    """检查用户角色"""
    async def role_checker(current_user: SessionData = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user
    return role_checker

# API密钥验证函数
def validate_api_key(api_key: str) -> bool:
    """
    验证API密钥格式是否有效
    
    :param api_key: 待验证的API密钥
    :return: 格式是否有效的布尔值
    """
    if not api_key or not isinstance(api_key, str):
        return False
    
    # DeepSeek API密钥通常是长度为40的字符串（类似UUID格式）
    import re
    api_key_pattern = r'^sk-[a-zA-Z0-9]{32,48}$'
    return bool(re.match(api_key_pattern, api_key))

# 兼容性JWT实现
def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

def _b64url_decode(data: str) -> bytes:
    pad = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)

def _normalize_payload(payload: dict) -> dict:
    pl = dict(payload)
    exp = pl.get("exp")
    if isinstance(exp, datetime):
        pl["exp"] = int(exp.timestamp())
    return pl

def safe_jwt_encode(payload: dict, secret: str) -> str:
    try:
        if hasattr(jwt, "encode"):
            return jwt.encode(_normalize_payload(payload), secret, algorithm="HS256")
    except Exception:
        pass
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = _b64url_encode(json.dumps(_normalize_payload(payload), separators=(',', ':')).encode('utf-8'))
    signing_input = f"{header_b64}.{payload_b64}".encode('ascii')
    signature = hmac.new(secret.encode('utf-8'), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def safe_jwt_decode(token: str, secret: str) -> dict:
    try:
        if hasattr(jwt, "decode"):
            return jwt.decode(token, secret, algorithms=["HS256"])
    except Exception:
        pass
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="无效的令牌")
        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode('ascii')
        expected_sig = hmac.new(secret.encode('utf-8'), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(expected_sig, _b64url_decode(sig_b64)):
            raise HTTPException(status_code=401, detail="令牌签名不匹配")
        payload = json.loads(_b64url_decode(payload_b64).decode('utf-8'))
        exp = payload.get("exp")
        if exp is not None and int(time.time()) > int(exp):
            raise HTTPException(status_code=401, detail="令牌已过期")
        return payload
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="无效的令牌")

# 在第1行的导入语句中添加 Depends
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
import jwt
import hashlib
import logging
from typing import List

from .models import (
    LoginRequest, LoginResponse, RegisterRequest, UserProfileResponse,
    UserPostsResponse, ErrorResponse
)
from backend.utils.db_users_core import ExtendedUserDatabase as UserDatabase
from backend.utils.auth import get_current_user, verify_token, get_password_hash, verify_password, safe_jwt_encode
from backend.utils.logger import get_logger

# 设置日志
logger = get_logger('auth_routes')  # 修复：使用get_logger替代setup_logger

# 添加调试信息，确认导入的UserDatabase来源
import inspect
logger.info(f"UserDatabase imported from: {inspect.getfile(UserDatabase)}")
logger.info(f"UserDatabase methods: {dir(UserDatabase)}")

# 实例化用户数据库
user_db = UserDatabase()
logger.info(f"user_db instance type: {type(user_db)}")
logger.info(f"user_db methods: {[method for method in dir(user_db) if not method.startswith('_')]}")

# 创建认证路由器
auth_router = APIRouter()

# OAuth2密码授权方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# 登录路由
@auth_router.post("/login", response_model=LoginResponse, responses={401: {"model": ErrorResponse}})
async def login(login_data: LoginRequest):
    try:
        # 从数据库中获取用户
        user = user_db.get_user_by_username(login_data.username)
        if not user:
            logger.warning(f"Login attempt with non-existent username: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 使用verify_user方法验证密码
        is_valid, error_msg = user_db.verify_user(login_data.username, login_data.password)
        if not is_valid:
            logger.warning(f"Invalid password for user: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查用户是否被封禁
        if user.get('is_banned', False):
            logger.warning(f"Login attempt with banned user: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账号已被封禁",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 创建JWT令牌
        access_token_expires = timedelta(days=7)
        # 修复：将datetime.now(datetime.timezone.utc)改为datetime.utcnow()
        expire = datetime.utcnow() + access_token_expires
        to_encode = {
            "sub": user['username'],
            "exp": expire,
            "user_id": user['id'],
            "is_admin": user.get('is_admin', False)
        }
        
        # 使用配置中的密钥
        from backend.config import settings
        encoded_jwt = safe_jwt_encode(to_encode, settings.jwt_secret_key)
        
        logger.info(f"User {login_data.username} logged in successfully")
        
        # 获取用户角色
        # 假设数据库中存储的是中文角色名称
        user_role = user.get('role', '使用者')  # 默认角色为'使用者'
        
        return {
            "success": True,
            "access_token": encoded_jwt,
            "token_type": "bearer",
            "user_id": user['id'],
            "username": user['username'],
            "is_admin": user.get('is_admin', False),
            "role": user_role  # 添加role字段，前端需要这个字段来决定重定向
        }
        
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录过程中发生错误",
        )

# 注册路由
@auth_router.post("/register", response_model=LoginResponse, responses={400: {"model": ErrorResponse}})
async def register(register_data: RegisterRequest):
    try:
        logger.info(f"开始注册用户: {register_data.username}")
        
        # 检查用户是否已存在
        existing_user = user_db.get_user_by_username(register_data.username)
        logger.info(f"检查用户名 {register_data.username} 是否存在: {existing_user is not None}")
        
        if existing_user:
            logger.warning(f"Registration attempt with existing username: {register_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在",
            )
        
        # 检查邮箱是否已存在
        existing_email = user_db.get_user_by_email(register_data.email)
        logger.info(f"检查邮箱 {register_data.email} 是否存在: {existing_email is not None}")
        
        if existing_email:
            logger.warning(f"Registration attempt with existing email: {register_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册",
            )
        
        # 创建新用户 - 直接传递原始密码，让add_user内部使用高级加密处理
        logger.info(f"开始创建用户: {register_data.username}")
        user_id = user_db.add_user(
            username=register_data.username,
            email=register_data.email,
            password=register_data.password,  # 直接传递原始密码，让add_user内部处理高级加密
            phone=register_data.phone,
            role="使用者",
            real_name=getattr(register_data, 'real_name', None),
            id_card=getattr(register_data, 'id_number', None)
        )
        logger.info(f"用户创建结果: user_id={user_id}")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="注册失败，可能是因为用户名或邮箱已存在",
            )
        
        # 为新用户创建JWT令牌
        access_token_expires = timedelta(days=7)
        expire = datetime.utcnow() + access_token_expires
        to_encode = {
            "sub": register_data.username,
            "exp": expire,
            # 修复：将id改为user_id
            "user_id": user_id,
            "is_admin": False
        }
        
        # 使用配置中的密钥
        from backend.config import settings
        encoded_jwt = safe_jwt_encode(to_encode, settings.jwt_secret_key)
        
        logger.info(f"New user registered: {register_data.username}")
        
        return {
            "success": True,  # 添加缺失的success字段
            "message": "注册成功！",  # 添加成功消息
            "access_token": encoded_jwt,
            "token_type": "bearer",
            # 修复：将id改为user_id
            "user_id": user_id,
            "username": register_data.username,
            "is_admin": False,
            "role": "使用者"
        }
        
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册过程中发生错误",
        )

# 获取用户资料路由
@auth_router.get("/user/profile", response_model=UserProfileResponse, responses={401: {"model": ErrorResponse}})
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    try:
        # 获取用户完整信息
        user = user_db.get_user_by_username(current_user.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 修复：将user['user_id']改为user['id']
        post_count = user_db.get_user_post_count(user['id'])
        collection_count = user_db.get_user_collection_count(user['id'])
        following_count = user_db.get_user_following_count(user['id'])
        followers_count = user_db.get_user_followers_count(user['id'])
        
        logger.info(f"User profile requested: {user['username']}")
        
        # 返回用户资料 - 按照UserProfileResponse模型结构组织数据
        return {
            "success": True,
            "user_info": {
                "user_id": user['id'],
                "username": user['username'],
                "email": user.get('email', ''),
                "phone": user.get('phone', ''),
                "avatar": user.get('avatar', ''),
                "bio": user.get('bio', ''),
                "gender": user.get('gender', ''),
                "birthday": user.get('birthday', ''),
                "created_at": user['created_at'],
                "is_admin": user.get('is_admin', False),
                "is_banned": user.get('is_banned', False),
                "post_count": post_count,
                "collection_count": collection_count,
                "following_count": following_count,
                "followers_count": followers_count
            },
            "message": "用户资料获取成功"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving user profile: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户资料时发生错误",
        )

# 获取用户帖子路由
@auth_router.get("/user/posts", response_model=UserPostsResponse, responses={401: {"model": ErrorResponse}})
async def get_user_posts(
    page: int = 1,
    page_size: int = 10,
    current_user: dict = Depends(get_current_user)
):
    try:
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 修复：先获取完整用户信息
        user = user_db.get_user_by_username(current_user.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 获取用户帖子
        posts = user_db.get_user_posts(user['id'], offset, page_size)
        total_posts = user_db.get_user_post_count(user['id'])
        
        # 格式化帖子数据
        formatted_posts = []
        for post in posts:
            formatted_posts.append({
                "post_id": post['post_id'],
                "title": post['title'],
                "content": post['content'],
                "category": post['category'],
                "created_at": post['created_at'],
                "likes_count": post.get('likes_count', 0),
                "comments_count": post.get('comments_count', 0),
                "status": post.get('status', 'pending')
            })
        
        logger.info(f"User posts requested: {current_user.username}, page: {page}")
        
        return {
            "success": True,
            "posts": formatted_posts,
            "total": total_posts,
            "message": f"成功获取用户帖子，共 {total_posts} 篇"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving user posts: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户帖子时发生错误",
        )

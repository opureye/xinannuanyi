# 在第1行的导入语句中添加 Depends
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
import logging
from typing import List, Dict, Any

from backend.api.models import (
    UserCollectionsResponse, AchievementResponse,
    AchievementsResponse, ErrorResponse, DeactivateUserRequest,
    UpdateProfileRequest, UpdateProfileResponse
)
from backend.utils.db_core import UserDatabase
from backend.utils.db_users_core import ExtendedUserDatabase as UserBasicDatabase
from backend.utils.db_articles import db as article_db
from backend.utils.db_comments import comments_db as comment_db
from backend.utils.db_collections import collections_db as collection_db
from backend.utils.db_follows import FollowDatabase
from backend.utils.auth import get_current_user, SessionData
from backend.utils.logger import get_logger

# 设置日志
logger = get_logger('user_routes')  # 修复：使用get_logger替代setup_logger

# 实例化用户数据库
user_db = UserDatabase()

# 创建用户路由器
user_router = APIRouter()

@user_router.get("/user/{username}/profile", response_model=Dict[str, Any], responses={404: {"model": ErrorResponse}})
async def get_public_user_profile(username: str):
    try:
        user = user_db.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

        post_count = user_db.get_user_post_count(user['id'])
        collection_count = user_db.get_user_collection_count(user['id'])
        following_count = user_db.get_user_following_count(user['id'])
        followers_count = user_db.get_user_followers_count(user['id'])

        return {
            "success": True,
            "user_info": {
                "username": user.get('username', username),
                "avatar": user.get('avatar', ''),
                "bio": user.get('bio', ''),
                "level": user.get('level', 1),
                "exp": user.get('experience', 0),
                "posts_count": post_count,
                "collections_count": collection_count,
                "following_count": following_count,
                "followers_count": followers_count,
                "likes_received": user.get('likes_count', 0),
                "helpful_posts": user.get('helpful_posts_count', 0),
                "created_at": user.get('created_at', '')
            },
            "message": "用户资料获取成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving public user profile: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取用户资料时发生错误")

@user_router.get("/user/{username}/posts", response_model=Dict[str, Any], responses={404: {"model": ErrorResponse}})
async def get_public_user_posts(username: str, page: int = 1, page_size: int = 10):
    try:
        user = user_db.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

        offset = (page - 1) * page_size
        posts = user_db.get_user_posts(user['id'], offset, page_size)
        total_posts = user_db.get_user_post_count(user['id'])
        formatted_posts = [{
            "post_id": post.get('post_id') or post.get('id'),
            "title": post.get('title', '未命名帖子'),
            "content": post.get('content', ''),
            "category": post.get('category', '未分类'),
            "created_at": post.get('created_at', ''),
            "likes_count": post.get('likes_count', 0),
            "comments_count": post.get('comments_count', 0),
            "status": post.get('status', 'approved')
        } for post in posts]

        return {
            "success": True,
            "posts": formatted_posts,
            "total": total_posts,
            "message": "用户帖子获取成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving public user posts: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取用户帖子时发生错误")

# 获取用户收藏路由
@user_router.get("/user/{username}/collections", response_model=UserCollectionsResponse, responses={404: {"model": ErrorResponse}})
async def get_user_collections(
    username: str,
    page: int = 1,
    page_size: int = 10,
    current_user: SessionData = Depends(get_current_user)
):
    try:
        # 检查请求的用户是否存在
        target_user = user_db.get_user_by_username(username)
        if not target_user:
            logger.warning(f"User not found: {username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 获取用户收藏
        collections = user_db.get_user_collections(target_user['id'], offset, page_size)
        total_collections = user_db.get_user_collection_count(target_user['id'])
        
        # 格式化收藏数据
        formatted_collections = []
        for item in collections:
            formatted_collections.append({
                "collection_id": item['collection_id'],
                "item_id": item['item_id'],
                "item_type": item['item_type'],
                "title": item['title'],
                "created_at": item['created_at']
            })
        
        # 修复：将字典访问改为点号访问
        logger.info(f"User collections requested: {username} by {current_user.username}")
        
        return {
            "success": True,
            "collections": formatted_collections,
            "total": total_collections,
            "message": "获取成功"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving user collections: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户收藏时发生错误",
        )

# 获取用户成就路由
@user_router.get("/achievements", response_model=AchievementsResponse, responses={401: {"model": ErrorResponse}})
async def get_user_achievements(current_user: SessionData = Depends(get_current_user)):
    try:
        # 获取当前用户完整信息
        user = user_db.get_user_by_username(current_user.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
            
        # 获取用户的成就
        achievements = user_db.get_user_achievements(user['id'])
        
        # 格式化成就数据
        formatted_achievements = []
        for achievement in achievements:
            formatted_achievements.append({
                "achievement_id": achievement['achievement_id'],
                "name": achievement['name'],
                "description": achievement['description'],
                "icon": achievement['icon'],
                "unlocked_at": achievement['unlocked_at'],
                "points": achievement['points']
            })
        
        logger.info(f"Achievements requested for user: {current_user.username}")
        
        return {
            "achievements": formatted_achievements,
            "total_points": sum(achievement['points'] for achievement in achievements)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving user achievements: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户成就时发生错误",
        )

# 解锁成就路由
@user_router.post("/achievements/{achievement_id}/unlock", response_model=AchievementResponse, responses={400: {"model": ErrorResponse}})
async def unlock_achievement(
    achievement_id: str,
    current_user: SessionData = Depends(get_current_user)
):
    try:
        # 获取当前用户完整信息
        user = user_db.get_user_by_username(current_user.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
            
        # 检查成就是否已解锁
        existing_achievement = user_db.check_user_achievement(user['id'], achievement_id)
        if existing_achievement:
            logger.warning(f"Achievement already unlocked: {achievement_id} by user: {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该成就已解锁",
            )
        
        # 解锁成就
        achievement = user_db.unlock_achievement(
            user_id=user['id'],
            achievement_id=achievement_id,
            unlocked_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        if not achievement:
            logger.warning(f"Invalid achievement ID: {achievement_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的成就ID",
            )
        
        logger.info(f"Achievement unlocked: {achievement_id} by user: {current_user.username}")
        
        return {
            "achievement_id": achievement['achievement_id'],
            "name": achievement['name'],
            "description": achievement['description'],
            "icon": achievement['icon'],
            "unlocked_at": achievement['unlocked_at'],
            "points": achievement['points']
        }
        
    except Exception as e:
        logger.error(f"Error unlocking achievement: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="解锁成就时发生错误",
        )

# 用户停用路由
@user_router.post("/user/deactivate", response_model=dict, responses={400: {"model": ErrorResponse}})
async def deactivate_user(
    deactivate_data: DeactivateUserRequest,
    current_user: SessionData = Depends(get_current_user)
):
    try:
        # 获取当前用户信息
        user = user_db.get_user_by_username(current_user.username)
        
        # 验证密码
        if not user_db.verify_user_password(user['id'], deactivate_data.password):
            logger.warning(f"Incorrect password for user deactivation: {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码错误",
            )
        
        # 停用账号
        user_db.deactivate_user(user['id'])
        
        logger.info(f"User deactivated: {current_user.username}")
        
        return {"detail": "账号已成功停用"}
        
    except Exception as e:
        logger.error(f"Error deactivating user: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="停用账号时发生错误",
        )

# 添加新API路由：获取用户帖子数量
@user_router.get("/user/posts/count", response_model=Dict[str, Any], responses={401: {"model": ErrorResponse}})
async def get_user_posts_count(current_user: SessionData = Depends(get_current_user)):
    try:
        # 获取当前用户完整信息
        user = user_db.get_user_by_username(current_user.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
            
        # 获取用户的帖子数量
        post_count = user_db.get_user_post_count(user['id'])
        
        logger.info(f"User posts count requested: {current_user.username}")
        
        return {
            "success": True,
            "count": post_count,
            "message": "获取成功"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving user posts count: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户帖子数量时发生错误",
        )

# 添加新API路由：获取用户收藏数量
@user_router.get("/user/collections/count", response_model=Dict[str, Any], responses={401: {"model": ErrorResponse}})
async def get_user_collections_count(current_user: SessionData = Depends(get_current_user)):
    try:
        # 获取当前用户完整信息
        user = user_db.get_user_by_username(current_user.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
            
        # 获取用户的收藏数量
        collection_count = user_db.get_user_collection_count(user['id'])
        
        logger.info(f"User collections count requested: {current_user.username}")
        
        return {
            "success": True,
            "count": collection_count,
            "message": "获取成功"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving user collections count: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户收藏数量时发生错误",
        )

# 添加新API路由：获取用户粉丝数量
@user_router.get("/user/followers/count", response_model=Dict[str, Any], responses={401: {"model": ErrorResponse}})
async def get_user_followers_count(current_user: SessionData = Depends(get_current_user)):
    try:
        # 获取当前用户完整信息
        user = user_db.get_user_by_username(current_user.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
            
        # 获取用户的粉丝数量
        followers_count = user_db.get_user_followers_count(user['id'])
        
        logger.info(f"User followers count requested: {current_user.username}")
        
        return {
            "success": True,
            "count": followers_count,
            "message": "获取成功"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving user followers count: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户粉丝数量时发生错误",
        )

# 添加新API路由：获取用户注册信息
@user_router.get("/user/registration", response_model=Dict[str, Any], responses={401: {"model": ErrorResponse}})
async def get_user_registration_info(current_user: SessionData = Depends(get_current_user)):
    try:
        # 修复：将字典访问改为点号访问
        user = user_db.get_user_by_username(current_user.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        
        # 检查用户是否已注册（其实总是已注册的，因为已经登录了）
        is_registered = True
        
        # 修复：将字典访问改为点号访问
        logger.info(f"User registration info requested: {current_user.username}")
        
        return {
            "success": True,
            "is_registered": is_registered,
            "created_at": user['created_at'],
            "message": "获取成功"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving user registration info: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户注册信息时发生错误",
        )
# 更新用户资料
@user_router.post("/user/profile/update", response_model=UpdateProfileResponse, responses={401: {"model": ErrorResponse}})
async def update_profile(request: UpdateProfileRequest, current_user: SessionData = Depends(get_current_user)):
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        if not update_data:
            return {"success": True, "message": "无可更新字段"}
        ok = user_db.update_user_profile(current_user.username, update_data)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="更新失败")
        logger.info(f"更新用户资料: {current_user.username}")
        return {"success": True, "message": "更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户资料时发生错误: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="服务器错误")
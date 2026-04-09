# 关注功能路由
import os
import sys

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取backend目录
backend_dir = os.path.dirname(current_dir)
# 获取项目根目录
project_root = os.path.dirname(backend_dir)

# 将项目根目录添加到Python路径
sys.path.insert(0, project_root)

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
import logging
from pydantic import BaseModel

from backend.utils.db_follows import (
    follow_user, unfollow_user, is_following, 
    get_user_following, get_user_followers
)
from backend.utils.auth import get_current_user, SessionData
from backend.utils.logger import get_logger
from .models import ErrorResponse

# 设置日志
logger = get_logger('follow_routes')

# 创建关注路由器
follow_router = APIRouter()

# 请求模型
class FollowRequest(BaseModel):
    follower: str
    following: str

class FollowResponse(BaseModel):
    success: bool
    message: str

class FollowCheckResponse(BaseModel):
    following: bool

# 检查关注状态路由
@follow_router.post("/follow/check", response_model=FollowCheckResponse, responses={400: {"model": ErrorResponse}})
async def check_follow_status(
    request: FollowRequest,
    current_user: SessionData = Depends(get_current_user)
):
    """
    检查用户是否已关注另一个用户
    """
    try:
        logger.info(f"检查关注状态 - 关注者: {request.follower}, 被关注者: {request.following}")
        
        # 检查关注状态
        following_status = is_following(request.follower, request.following)
        
        logger.info(f"关注状态检查结果: {following_status}")
        
        return FollowCheckResponse(following=following_status)
        
    except Exception as e:
        logger.error(f"检查关注状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="检查关注状态失败"
        )

# 关注用户路由
@follow_router.post("/follow/add", response_model=FollowResponse, responses={400: {"model": ErrorResponse}})
async def add_follow(
    request: FollowRequest,
    current_user: SessionData = Depends(get_current_user)
):
    """
    关注用户
    """
    try:
        logger.info(f"用户关注 - 关注者: {request.follower}, 被关注者: {request.following}")
        
        # 验证当前用户是否为关注者
        if current_user.username != request.follower:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能以自己的身份关注其他用户"
            )
        
        # 执行关注操作
        result = follow_user(request.follower, request.following)
        
        if result["success"]:
            logger.info(f"关注成功: {request.follower} -> {request.following}")
            return FollowResponse(success=True, message=result["message"])
        else:
            logger.warning(f"关注失败: {result['message']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"关注用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="关注用户失败"
        )

# 取消关注路由
@follow_router.post("/follow/remove", response_model=FollowResponse, responses={400: {"model": ErrorResponse}})
async def remove_follow(
    request: FollowRequest,
    current_user: SessionData = Depends(get_current_user)
):
    """
    取消关注用户
    """
    try:
        logger.info(f"取消关注 - 关注者: {request.follower}, 被关注者: {request.following}")
        
        # 验证当前用户是否为关注者
        if current_user.username != request.follower:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能取消自己的关注"
            )
        
        # 执行取消关注操作
        result = unfollow_user(request.follower, request.following)
        
        if result["success"]:
            logger.info(f"取消关注成功: {request.follower} -> {request.following}")
            return FollowResponse(success=True, message=result["message"])
        else:
            logger.warning(f"取消关注失败: {result['message']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消关注失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取消关注失败"
        )

# 获取用户关注列表路由
@follow_router.get("/user/{username}/following", response_model=List[Dict[str, Any]], responses={404: {"model": ErrorResponse}})
async def get_following_list(
    username: str,
    current_user: SessionData = Depends(get_current_user)
):
    """
    获取用户关注列表
    """
    try:
        logger.info(f"获取关注列表 - 用户: {username}")
        
        following_list = get_user_following(username)
        
        logger.info(f"获取关注列表成功，共 {len(following_list)} 个关注")
        
        return following_list
        
    except Exception as e:
        logger.error(f"获取关注列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取关注列表失败"
        )

# 获取用户粉丝列表路由
@follow_router.get("/user/{username}/followers", response_model=List[Dict[str, Any]], responses={404: {"model": ErrorResponse}})
async def get_followers_list(
    username: str,
    current_user: SessionData = Depends(get_current_user)
):
    """
    获取用户粉丝列表
    """
    try:
        logger.info(f"获取粉丝列表 - 用户: {username}")
        
        followers_list = get_user_followers(username)
        
        logger.info(f"获取粉丝列表成功，共 {len(followers_list)} 个粉丝")
        
        return followers_list
        
    except Exception as e:
        logger.error(f"获取粉丝列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取粉丝列表失败"
        )
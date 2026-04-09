# 确保正确的导入
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

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from datetime import datetime
import logging
from typing import List

from .models import (
    UserListResponse, ErrorResponse, SearchUsersRequest,
    SearchUsersResponse, PendingArticlesResponse, AuditArticleRequest,
    ArticleAuditResponse
)
# 修复：直接从具体模块导入数据库功能，避免导入整个database模块
from backend.utils.db_users import users_db
from backend.utils.db_articles import add_article, get_article_by_id, get_pending_articles, update_article_status
from backend.utils.auth import get_current_user, require_role  # 确保导入require_role
from backend.utils.logger import get_logger  # 修复：使用get_logger替代setup_logger
from backend.utils.lock_manager import lock_manager  # 导入锁管理器

# 设置日志
logger = get_logger('admin_routes')  # 修复：使用get_logger替代setup_logger

# 创建管理员路由器，设置前缀
admin_router = APIRouter(prefix="/admin")

# 释放账号审核锁的路由
@admin_router.post("/audit/lock/release", response_model=dict, responses={400: {"model": ErrorResponse}})
async def release_audit_lock(
    current_user = Depends(get_current_user),
    _ = Depends(require_role('管理员'))
):
    try:
        lock_name = "account_audit_lock"
        
        # 尝试释放锁（只有锁的持有者才能释放）
        if lock_manager.release_lock(lock_name, current_user.username):
            logger.info(f"Admin {current_user.username} successfully released account audit lock")
            return {"detail": "账号审核锁已成功释放"}
        else:
            # 尝试强制释放锁
            if lock_manager.force_release_lock(lock_name):
                logger.warning(f"Admin {current_user.username} forcefully released account audit lock")
                return {"detail": "账号审核锁已被强制释放"}
            else:
                logger.info(f"Admin {current_user.username} tried to release account audit lock, but it's not locked")
                return {"detail": "账号审核锁未锁定"}
                
    except Exception as e:
        logger.error(f"Error releasing account audit lock: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="释放账号审核锁时发生错误"
        )

# 封禁用户路由（已修复）
@admin_router.post("/user/ban", response_model=dict, responses={400: {"model": ErrorResponse}})
async def ban_user(
    username: str = Body(..., embed=True),  # 使用Body参数接收用户名
    current_user = Depends(require_role('管理员'))  # 移除dict类型注解
):
    try:
        # 尝试获取账号审核锁
        lock_name = "account_audit_lock"
        if not lock_manager.get_lock(lock_name, current_user.username):
            # 检查锁状态
            lock_info = lock_manager.check_lock(lock_name)
            logger.warning(f"Admin {current_user.username} tried to ban user {username}, but account review is locked by {lock_info['locked_by'] if lock_info else 'unknown'}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="系统繁忙，请稍后再试"
            )
            
        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名不能为空",
            )
        
        # 检查用户是否存在
        user = users_db.get_user_by_username(username)
        if not user:
            logger.warning(f"User not found for ban: {username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户不存在",
            )
        
        # 修复：使用正确的字段名'id'而不是'user_id'
        user_id = user['id']
        users_db.ban_user(user_id)
        
        # 修复：使用对象属性访问方式
        logger.info(f"User banned: {username} by admin: {current_user.username}")
        
        return {"detail": "用户已成功封禁"}
        
    except Exception as e:
        logger.error(f"Error banning user: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="封禁用户时发生错误",
        )

# 解封用户路由
@admin_router.post("/user/unban", response_model=dict, responses={400: {"model": ErrorResponse}})
async def unban_user(
    username: str = Body(..., embed=True),  # 修复：添加Body(..., embed=True)确保正确解析
    current_user = Depends(require_role('管理员'))  # 移除dict类型注解，使用中文'管理员'
):
    try:
        # 尝试获取账号审核锁
        lock_name = "account_audit_lock"
        if not lock_manager.get_lock(lock_name, current_user.username):
            # 检查锁状态
            lock_info = lock_manager.check_lock(lock_name)
            logger.warning(f"Admin {current_user.username} tried to unban user {username}, but account review is locked by {lock_info['locked_by'] if lock_info else 'unknown'}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="系统繁忙，请稍后再试"
            )
            
        # 检查用户是否存在
        user = users_db.get_user_by_username(username)
        if not user:
            logger.warning(f"User not found for unban: {username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户不存在",
            )
        
        # 修复：使用正确的字段名'id'而不是'user_id'
        user_id = user['id']
        users_db.unban_user(user_id)
        
        # 修复：使用对象属性访问方式
        logger.info(f"User unbanned: {username} by admin: {current_user.username}")
        
        return {"detail": "用户已成功解封"}
        
    except Exception as e:
        logger.error(f"Error unbanning user: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="解封用户时发生错误",
        )

# 删除用户路由（只保留一个定义）
@admin_router.delete("/user/delete", response_model=dict, responses={400: {"model": ErrorResponse}})
async def delete_user(
    username: str,
    current_user = Depends(get_current_user),  # 移除dict类型注解
    _ = Depends(require_role('管理员'))  # 使用中文'管理员'，移除未使用的变量
):
    try:
        # 尝试获取账号审核锁
        lock_name = "account_audit_lock"
        if not lock_manager.get_lock(lock_name, current_user.username):
            # 检查锁状态
            lock_info = lock_manager.check_lock(lock_name)
            logger.warning(f"Admin {current_user.username} tried to delete user {username}, but account review is locked by {lock_info['locked_by'] if lock_info else 'unknown'}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="系统繁忙，请稍后再试"
            )
            
        # 检查用户是否存在
        user = users_db.get_user_by_username(username)
        if not user:
            logger.warning(f"User not found for deletion: {username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户不存在",
            )
        
        # 检查是否尝试删除管理员
        if user.get('role') == '管理员':
            # 修复：使用对象属性访问方式
            logger.warning(f"Attempt to delete admin user: {username} by {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除管理员用户",
            )
        
        # 删除用户
        users_db.delete_user(user['id'])
        
        # 修复：使用对象属性访问方式
        logger.info(f"User deleted: {username} by admin: {current_user.username}")
        
        return {"detail": "用户已成功删除"}
        
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户时发生错误",
        )

# 修改get_all_users路由
@admin_router.get("/users", response_model=UserListResponse, responses={400: {"model": ErrorResponse}})
async def get_all_users(
    page: int = 1,
    page_size: int = 20,
    current_user = Depends(get_current_user),
    _ = Depends(require_role('管理员'))
):
    try:
        # 尝试获取账号审核锁
        lock_name = "account_audit_lock"
        if not lock_manager.get_lock(lock_name, current_user.username):
            # 检查锁状态
            lock_info = lock_manager.check_lock(lock_name)
            logger.warning(f"Admin {current_user.username} tried to access account review, but it's locked by {lock_info['locked_by'] if lock_info else 'unknown'}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="系统繁忙，请稍后再试"
            )
            
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 获取所有用户
        users = users_db.get_all_users(offset, page_size)
        total_users = users_db.get_total_users_count()
        
        # 格式化用户数据
        formatted_users = []
        for user in users:
            # 确保phone字段是字符串
            phone_value = user.get('phone', '')
            phone_str = str(phone_value) if phone_value is not None else ''
            
            # 修复：直接使用数据库层已经计算好的is_banned字段
            formatted_users.append({
                "user_id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "phone": phone_str,
                "created_at": user['created_at'],
                "role": user.get('role', '使用者'),
                "is_admin": user.get('is_admin', False),
                "is_banned": user.get('is_banned', False)  # 直接使用数据库层计算的值
            })
        
        # 修复：使用对象属性访问方式
        logger.info(f"All users requested by admin: {current_user.username}, page: {page}")
        
        return {
            "success": True,
            "message": "获取用户列表成功",
            "users": formatted_users,
            "total": total_users,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_users + page_size - 1) // page_size
        }
        
    except Exception as e:
        logger.error(f"Error retrieving all users: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取所有用户时发生错误",
        )



# 修改search_users路由
@admin_router.post("/users/search", response_model=SearchUsersResponse, responses={400: {"model": ErrorResponse}})
async def search_users(
    search_data: SearchUsersRequest,
    current_user = Depends(get_current_user),
    _ = Depends(require_role('管理员'))
):
    try:
        # 尝试获取账号审核锁
        lock_name = "account_audit_lock"
        if not lock_manager.get_lock(lock_name, current_user.username):
            # 检查锁状态
            lock_info = lock_manager.check_lock(lock_name)
            logger.warning(f"Admin {current_user.username} tried to search users during account review, but it's locked by {lock_info['locked_by'] if lock_info else 'unknown'}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="系统繁忙，请稍后再试"
            )
            
        # 修复：使用正确的命名参数传递搜索关键词
        users = users_db.search_users(username=search_data.keyword)
        
        total_users = len(users) if users else 0
        
        # 应用分页
        page = search_data.page or 1
        page_size = search_data.page_size or 10
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_users = users[start_idx:end_idx] if users else []
        
        # 格式化用户数据
        formatted_users = []
        for user in paginated_users:
            # 确保phone字段是字符串
            phone_value = user.get('phone', '')
            phone_str = str(phone_value) if phone_value is not None else ''
            
            # 修复：直接使用数据库层已经计算好的is_banned字段
            formatted_users.append({
                "user_id": user.get('id', 0),  # 修复：使用正确的id字段
                "username": user['username'],
                "email": user.get('email', ''),
                "phone": phone_str,
                "created_at": user['created_at'],
                "role": user.get('role', '使用者'),
                "is_admin": user.get('is_admin', False),
                "is_banned": user.get('is_banned', False)  # 直接使用数据库层计算的值
            })
        
        # 修复：使用对象属性访问方式
        logger.info(f"Users searched by admin: {current_user.username}, keyword: {search_data.keyword}")
        
        return {
            "success": True,
            "message": "搜索用户成功",
            "users": formatted_users,
            "total": total_users,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_users + page_size - 1) // page_size
        }
        
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索用户时发生错误: {str(e)}"
        )

# 获取待审核文章路由（修复缺少的参数）
@admin_router.get("/articles/pending", response_model=PendingArticlesResponse, responses={400: {"model": ErrorResponse}})
async def admin_get_pending_articles(  # 修改函数名，避免冲突
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role('管理员'))  # 使用中文'管理员'
):
    try:
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 修复：调用正确的数据库函数，移除await关键字（这是同步函数）
        articles = get_pending_articles()
        # 如果需要分页，对结果进行分页处理
        paginated_articles = articles[offset:offset + page_size]
        total_articles = len(articles)
        
        # 格式化文章数据
        formatted_articles = []
        for article in paginated_articles:
            # 获取作者信息
            author = users_db.get_user_by_username(article['author'])
            
            formatted_articles.append({
                "id": article['id'],
                "title": article['title'],
                "content_preview": article['content'][:100] + ("..." if len(article['content']) > 100 else ""),
                "category": article.get('category', ''),
                "created_at": article['created_at'],
                "author_username": author['username'] if author else "未知"
            })
        
        # 修改这一行，将字典访问语法改为点语法
        logger.info(f"Pending articles requested by admin: {current_user.username}, page: {page}")
        
        return {
            "success": True,
            "articles": formatted_articles,
            "total": total_articles,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_articles + page_size - 1) // page_size,
            "message": "获取待审核文章成功"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving pending articles: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取待审核文章时发生错误",
        )

# 审核文章路由
@admin_router.post("/article/audit", response_model=ArticleAuditResponse, responses={400: {"model": ErrorResponse}})
async def audit_article(
    article_id: int = Body(..., embed=True),
    audit_status: str = Body(..., embed=True),
    current_user: dict = Depends(require_role('管理员'))  # 使用中文'管理员'
):
    try:
        # 检查文章是否存在
        article = get_article_by_id(article_id)
        if not article:
            logger.warning(f"Article not found for audit: {article_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文章不存在",
            )
        
        # 检查文章是否已审核
        if article.get('status') != 'pending':
            logger.warning(f"Article already audited: {article_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文章已审核",
            )
        
        # 修复：使用正确导入的update_article_status函数
        success = update_article_status(article_id, audit_status)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="审核操作失败"
            )
        
        logger.info(f"Article audited: {article_id} by admin: {current_user.username}, status: {audit_status}")
        
        return {
            "success": True,
            "article_id": article_id,
            "status": audit_status,
            "audited_at": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            "audited_by": current_user.username,
            "message": "文章审核成功"
        }
        
    except Exception as e:
        logger.error(f"Error auditing article: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="审核文章时发生错误",
        )
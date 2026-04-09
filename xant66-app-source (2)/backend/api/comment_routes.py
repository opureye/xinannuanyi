# 评论相关的API路由
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from backend.utils.db_comments import UserDatabase as CommentDatabase
from backend.utils.db_users_core import ExtendedUserDatabase as UserDatabase
from backend.utils.auth import get_current_user, get_current_user_optional, SessionData
from backend.utils.logger import get_logger

# 设置日志
logger = get_logger('comment_routes')

# 创建评论路由器
comment_router = APIRouter()

@comment_router.post("/articles/{article_id}/comments", response_model=Dict[str, Any])
async def add_comment(
    article_id: int,
    comment_data: Dict[str, Any],
    current_user: SessionData = Depends(get_current_user)
):
    """
    为文章添加评论
    """
    try:
        content = comment_data.get("content", "").strip()
        
        # 验证输入
        if not content:
            logger.warning(f"[评论添加失败] 评论内容为空 - 用户: {current_user.username}")
            raise HTTPException(status_code=400, detail="评论内容不能为空")
        
        if len(content) > 1000:
            logger.warning(f"[评论添加失败] 评论内容过长 - 用户: {current_user.username}, 长度: {len(content)}")
            raise HTTPException(status_code=400, detail="评论内容不能超过1000个字符")
        
        # 获取用户ID
        comment_db = CommentDatabase()
        user_db = UserDatabase()
        user_info = user_db.get_user_by_username(current_user.username)
        if not user_info:
            logger.error(f"[评论添加失败] 用户不存在 - 用户名: {current_user.username}")
            raise HTTPException(status_code=404, detail="用户不存在")
        
        user_id = user_info['id']
        
        # 检查文章是否存在
        with comment_db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
            if not cursor.fetchone():
                logger.warning(f"[评论添加失败] 文章不存在 - 文章ID: {article_id}")
                raise HTTPException(status_code=404, detail="文章不存在")
        
        # 添加评论
        comment_id = comment_db.add_comment(user_id, article_id, content)
        
        if comment_id:
            logger.info(f"[评论添加成功] 评论ID: {comment_id}, 用户: {current_user.username}, 文章ID: {article_id}")
            return {
                "status": "success",
                "comment_id": comment_id,
                "message": "评论提交成功，等待审核"
            }
        else:
            logger.error(f"[评论添加失败] 数据库添加评论失败 - 用户: {current_user.username}, 文章ID: {article_id}")
            raise HTTPException(status_code=500, detail="评论添加失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[评论添加错误] 添加评论时发生错误 - 文章ID: {article_id}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="评论添加失败")

@comment_router.get("/articles/{article_id}/comments", response_model=Dict[str, Any])
async def get_article_comments(
    article_id: int,
    current_user: Optional[SessionData] = Depends(get_current_user_optional)
):
    """
    获取文章的所有已批准评论
    """
    try:
        logger.info(f"[获取评论] 获取文章评论 - 文章ID: {article_id}")
        
        comment_db = CommentDatabase()
        user_db = UserDatabase()
        
        # 检查文章是否存在
        with comment_db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
            if not cursor.fetchone():
                logger.warning(f"[获取评论失败] 文章不存在 - 文章ID: {article_id}")
                raise HTTPException(status_code=404, detail="文章不存在")
        
        # 获取评论列表
        comments = comment_db.get_comments_by_article(article_id)
        
        # 获取当前用户ID（如果已登录）
        current_user_id = None
        if current_user:
            user_info = user_db.get_user_by_username(current_user.username)
            if user_info:
                current_user_id = user_info['id']
        
        # 为每个评论添加点赞数量和用户点赞状态
        for comment in comments:
            comment_id = comment['id']
            comment['like_count'] = comment_db.get_comment_like_count(comment_id)
            comment['is_liked'] = False
            if current_user_id:
                comment['is_liked'] = comment_db.is_comment_liked_by_user(current_user_id, comment_id)
        
        logger.info(f"[获取评论成功] 文章ID: {article_id}, 评论数量: {len(comments)}")
        
        return {
            "status": "success",
            "comments": comments,
            "count": len(comments)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[获取评论错误] 获取评论时发生错误 - 文章ID: {article_id}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取评论失败")

@comment_router.post("/comments/{comment_id}/like", response_model=Dict[str, Any])
async def toggle_comment_like(
    comment_id: int,
    current_user: SessionData = Depends(get_current_user)
):
    """
    切换评论点赞状态
    """
    try:
        logger.info(f"[评论点赞] 切换评论点赞 - 用户: {current_user.username}, 评论ID: {comment_id}")
        
        comment_db = CommentDatabase()
        user_db = UserDatabase()
        
        # 获取用户ID
        user_info = user_db.get_user_by_username(current_user.username)
        if not user_info:
            logger.error(f"[评论点赞失败] 用户不存在 - 用户名: {current_user.username}")
            raise HTTPException(status_code=404, detail="用户不存在")
        
        user_id = user_info['id']
        
        # 切换点赞状态
        result = comment_db.toggle_comment_like(user_id, comment_id)
        
        if result is not None:
            # 获取更新后的点赞数量
            like_count = comment_db.get_comment_like_count(comment_id)
            
            action = "点赞" if result else "取消点赞"
            logger.info(f"[评论点赞成功] {action} - 用户: {current_user.username}, 评论ID: {comment_id}, 点赞数: {like_count}")
            return {
                "status": "success",
                "liked": result,
                "like_count": like_count,
                "message": f"{action}成功"
            }
        else:
            logger.error(f"[评论点赞失败] 点赞操作失败 - 用户: {current_user.username}, 评论ID: {comment_id}")
            raise HTTPException(status_code=500, detail="点赞操作失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[评论点赞错误] 点赞时发生错误 - 评论ID: {comment_id}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="点赞操作失败")

@comment_router.get("/comments/pending", response_model=Dict[str, Any])
async def get_pending_comments(current_user: SessionData = Depends(get_current_user)):
    """
    获取待审核的评论列表（仅管理员可访问）
    """
    try:
        logger.info(f"[获取待审核评论] 用户: {current_user.username}")
        
        # 检查用户权限
        user_db = UserDatabase()
        user_info = user_db.get_user_by_username(current_user.username)
        if not user_info or user_info.get('role') != '管理员':
            logger.warning(f"[获取待审核评论失败] 权限不足 - 用户: {current_user.username}")
            raise HTTPException(status_code=403, detail="权限不足")
        
        comment_db = CommentDatabase()
        
        # 获取待审核评论
        with comment_db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.user_id, c.article_id, c.content, c.created_at, c.status,
                       u.username, a.title as article_title
                FROM comments c 
                JOIN users u ON c.user_id = u.id 
                JOIN articles a ON c.article_id = a.id
                WHERE c.status = 'pending'
                ORDER BY c.created_at ASC
            """)
            
            comments = cursor.fetchall()
            
            # 格式化结果
            results = []
            for comment in comments:
                results.append({
                    "id": comment[0],
                    "user_id": comment[1],
                    "article_id": comment[2],
                    "content": comment[3],
                    "created_at": comment[4],
                    "status": comment[5],
                    "username": comment[6],
                    "article_title": comment[7]
                })
        
        logger.info(f"[获取待审核评论成功] 找到 {len(results)} 条待审核评论")
        
        return {
            "status": "success",
            "comments": results,
            "count": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[获取待审核评论错误] 获取待审核评论时发生错误 - 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取待审核评论失败")

@comment_router.post("/comments/{comment_id}/audit", response_model=Dict[str, Any])
async def audit_comment(
    comment_id: int,
    audit_data: Dict[str, Any],
    current_user: SessionData = Depends(get_current_user)
):
    """
    审核评论（通过或拒绝）
    """
    try:
        action = audit_data.get("action", "").strip()
        
        logger.info(f"[审核评论] 用户: {current_user.username}, 评论ID: {comment_id}, 操作: {action}")
        
        # 检查用户权限
        user_db = UserDatabase()
        user_info = user_db.get_user_by_username(current_user.username)
        if not user_info or user_info.get('role') != '管理员':
            logger.warning(f"[审核评论失败] 权限不足 - 用户: {current_user.username}")
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 验证操作类型
        if action not in ["approve", "reject"]:
            logger.warning(f"[审核评论失败] 无效的操作类型 - 操作: {action}")
            raise HTTPException(status_code=400, detail="无效的操作类型")
        
        comment_db = CommentDatabase()
        
        # 检查评论是否存在且为待审核状态
        with comment_db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, status FROM comments WHERE id = ?", (comment_id,))
            comment = cursor.fetchone()
            
            if not comment:
                logger.warning(f"[审核评论失败] 评论不存在 - 评论ID: {comment_id}")
                raise HTTPException(status_code=404, detail="评论不存在")
            
            if comment[1] != 'pending':
                logger.warning(f"[审核评论失败] 评论已审核 - 评论ID: {comment_id}, 状态: {comment[1]}")
                raise HTTPException(status_code=400, detail="评论已审核")
        
        # 更新评论状态
        new_status = "approved" if action == "approve" else "rejected"
        success = comment_db.update_comment_status(comment_id, new_status)
        
        if success:
            action_text = "通过" if action == "approve" else "拒绝"
            logger.info(f"[审核评论成功] 评论ID: {comment_id}, 操作: {action_text}, 审核人: {current_user.username}")
            return {
                "status": "success",
                "comment_id": comment_id,
                "action": action,
                "new_status": new_status,
                "message": f"评论{action_text}成功"
            }
        else:
            logger.error(f"[审核评论失败] 更新评论状态失败 - 评论ID: {comment_id}")
            raise HTTPException(status_code=500, detail="审核操作失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[审核评论错误] 审核评论时发生错误 - 评论ID: {comment_id}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="审核评论失败")
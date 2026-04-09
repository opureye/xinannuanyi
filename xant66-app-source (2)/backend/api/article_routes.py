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

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from backend.utils.db_articles import UserDatabase
from backend.utils.logger import get_logger
from backend.utils.auth import get_current_user, SessionData

router = APIRouter()
logger = get_logger(__name__)

@router.post("/articles/submit", response_model=Dict[str, Any])
async def submit_article(
    article_data: Dict[str, Any], 
    current_user: SessionData = Depends(get_current_user)
):
    """
    提交新文章
    """
    try:
        # 全面记录接收到的数据
        logger.info(f"[文章提交] 收到新的文章提交请求 - 用户名: {current_user.username}, 角色: {current_user.role}")
        logger.debug(f"[文章提交] 请求数据详情: {article_data}")
        
        # 提取并验证数据
        title = article_data.get("title", "").strip()
        content = article_data.get("content", "").strip()
        category = article_data.get("category", "").strip()
        
        # 详细日志记录
        logger.info(f"[文章提交] 文章信息 - 标题: '{title[:50]}...', 长度: {len(title)}, 内容长度: {len(content)}, 分类: {category}")
        
        # 验证输入
        if not title:
            logger.warning(f"[文章提交失败] 标题为空 - 用户: {current_user.username}")
            raise HTTPException(status_code=400, detail="文章标题不能为空")
        
        if not content:
            logger.warning(f"[文章提交失败] 内容为空 - 用户: {current_user.username}")
            raise HTTPException(status_code=400, detail="文章内容不能为空")
        
        if not category:
            logger.warning(f"[文章提交失败] 分类未选择 - 用户: {current_user.username}")
            raise HTTPException(status_code=400, detail="请选择文章分类")
        
        # 限制标题和内容长度
        if len(title) > 200:
            logger.warning(f"[文章提交失败] 标题过长 - 用户: {current_user.username}, 长度: {len(title)}")
            raise HTTPException(status_code=400, detail="文章标题不能超过200个字符")
        
        if len(content) > 10000:
            logger.warning(f"[文章提交失败] 内容过长 - 用户: {current_user.username}, 长度: {len(content)}")
            raise HTTPException(status_code=400, detail="文章内容不能超过10000个字符")
        
        # 添加文章到数据库
        try:
            user_db = UserDatabase()
            logger.info(f"[文章存储] 准备添加文章到数据库 - 用户: {current_user.username}")
            
            article_id = user_db.add_article(title, content, current_user.username, category)
            
            if article_id:
                logger.info(f"[文章存储成功] 文章已成功添加到数据库 - ID: {article_id}, 用户: {current_user.username}")
                return {
                    "status": "success",
                    "article_id": article_id,
                    "message": "文章提交成功，等待审核"
                }
            else:
                logger.error(f"[文章存储失败] 数据库添加文章返回空ID - 用户: {current_user.username}")
                raise HTTPException(status_code=500, detail="文章添加失败，请稍后重试")
        except Exception as db_error:
            logger.error(f"[数据库错误] 添加文章时发生异常 - 用户: {current_user.username}, 错误: {str(db_error)}")
            raise HTTPException(status_code=500, detail=f"数据库操作失败: {str(db_error)}")
            
    except HTTPException as http_error:
        # 重新抛出HTTP异常以保留原始状态码
        raise
    except Exception as e:
        logger.error(f"[系统错误] 文章提交过程中发生未预期错误 - 用户: {current_user.username}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误，请联系管理员")

@router.get("/articles", response_model=Dict[str, Any])
async def get_articles(
    page: int = 1,
    page_size: int = 10,
    category: str = None,
    status: str = "approved",
    search: str = None
):
    """
    获取文章列表，支持分页、分类筛选和搜索
    """
    try:
        logger.info(f"[文章列表] 获取文章列表 - 页码: {page}, 每页: {page_size}, 分类: {category}, 状态: {status}, 搜索: {search}")
        
        user_db = UserDatabase()
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 使用安全的查询验证和清理
        from backend.utils.sql_security import validate_search_input, SQLSecurityValidator
        
        # 验证状态值（只允许预定义的状态）
        allowed_statuses = ['pending', 'approved', 'rejected']
        if status not in allowed_statuses:
            status = 'approved'
            logger.warning(f"无效的状态值，使用默认值: approved")
        
        # 构建查询条件（使用参数化查询，列名硬编码以确保安全）
        where_conditions = ["status = ?"]
        params = [status]
        
        if category:
            # 验证和清理分类输入
            is_valid, error = SQLSecurityValidator.validate_string(category, max_length=50)
            if is_valid:
                where_conditions.append("category = ?")
                params.append(category)
            else:
                logger.warning(f"无效的分类输入: {error}")
            
        if search:
            # 验证和清理搜索输入
            search_term = validate_search_input(search, max_length=200)
            if search_term:
                search_pattern = f"%{search_term}%"
                where_conditions.append("(title LIKE ? OR content LIKE ?)")
                params.extend([search_pattern, search_pattern])
        
        # 使用AND连接所有条件（列名已硬编码，安全）
        where_clause = " AND ".join(where_conditions)
        
        # 获取文章列表
        with user_db._get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取总数（使用参数化查询）
            count_query = f"SELECT COUNT(*) FROM articles WHERE {where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]
            
            # 获取文章列表（使用参数化查询）
            query = f"""
                SELECT id, title, content, author, category, created_at, updated_at, 
                       view_count, like_count, status
                FROM articles 
                WHERE {where_clause}
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """
            cursor.execute(query, params + [page_size, offset])
            articles = cursor.fetchall()
            
            # 格式化结果
            article_list = []
            for article in articles:
                article_dict = {
                    "id": article[0],
                    "title": article[1],
                    "content": article[2][:200] + "..." if len(article[2]) > 200 else article[2],  # 摘要
                    "author": article[3],
                    "category": article[4],
                    "created_at": article[5],
                    "updated_at": article[6],
                    "view_count": article[7],
                    "like_count": article[8],
                    "status": article[9]
                }
                article_list.append(article_dict)
            
            # 计算总页数
            total_pages = (total_count + page_size - 1) // page_size
            
            logger.info(f"[文章列表成功] 返回 {len(article_list)} 篇文章，总计 {total_count} 篇")
            
            return {
                "status": "success",
                "articles": article_list,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
            
    except Exception as e:
        logger.error(f"[文章列表错误] 获取文章列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取文章列表失败")

@router.get("/articles/{article_id}", response_model=Dict[str, Any])
async def get_article_detail(article_id: int):
    """
    获取文章详情
    """
    try:
        logger.info(f"[文章详情] 获取文章详情 - ID: {article_id}")
        
        user_db = UserDatabase()
        
        with user_db._get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取文章详情
            cursor.execute("""
                SELECT id, title, content, author, category, created_at, updated_at, 
                       view_count, like_count, status, helpful_count, unhelpful_count
                FROM articles 
                WHERE id = ?
            """, (article_id,))
            
            article = cursor.fetchone()
            
            if not article:
                logger.warning(f"[文章详情] 文章不存在 - ID: {article_id}")
                raise HTTPException(status_code=404, detail="文章不存在")
            
            # 增加浏览量
            cursor.execute("UPDATE articles SET view_count = view_count + 1 WHERE id = ?", (article_id,))
            conn.commit()
            
            # 格式化结果
            article_dict = {
                "id": article[0],
                "title": article[1],
                "content": article[2],
                "author": article[3],
                "category": article[4],
                "created_at": article[5],
                "updated_at": article[6],
                "view_count": article[7] + 1,  # 包含刚增加的浏览量
                "like_count": article[8],
                "status": article[9],
                "helpful_count": article[10],
                "unhelpful_count": article[11]
            }
            
            logger.info(f"[文章详情成功] 返回文章详情 - ID: {article_id}, 标题: {article[1]}")
            
            return {
                "status": "success",
                "article": article_dict
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[文章详情错误] 获取文章详情失败 - ID: {article_id}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取文章详情失败")

@router.get("/articles/categories", response_model=Dict[str, Any])
async def get_article_categories():
    """
    获取所有文章分类
    """
    try:
        logger.info("[文章分类] 获取文章分类列表")
        
        user_db = UserDatabase()
        
        with user_db._get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取所有分类及其文章数量
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM articles 
                WHERE status = 'approved' AND category != ''
                GROUP BY category
                ORDER BY count DESC
            """)
            
            categories = cursor.fetchall()
            
            category_list = []
            for category in categories:
                category_list.append({
                    "name": category[0],
                    "count": category[1]
                })
            
            logger.info(f"[文章分类成功] 返回 {len(category_list)} 个分类")
            
            return {
                "status": "success",
                "categories": category_list
            }
            
    except Exception as e:
        logger.error(f"[文章分类错误] 获取分类列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取分类列表失败")

@router.post("/articles/{article_id}/like", response_model=Dict[str, Any])
async def like_article(
    article_id: int,
    current_user: SessionData = Depends(get_current_user)
):
    """
    点赞文章
    """
    try:
        logger.info(f"[文章点赞] 用户点赞文章 - 用户: {current_user.username}, 文章ID: {article_id}")
        
        user_db = UserDatabase()
        
        with user_db._get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查文章是否存在
            cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="文章不存在")
            
            # 增加点赞数
            cursor.execute("UPDATE articles SET like_count = like_count + 1 WHERE id = ?", (article_id,))
            conn.commit()
            
            # 获取更新后的点赞数
            cursor.execute("SELECT like_count FROM articles WHERE id = ?", (article_id,))
            new_like_count = cursor.fetchone()[0]
            
            logger.info(f"[文章点赞成功] 文章ID: {article_id}, 新点赞数: {new_like_count}")
            
            return {
                "status": "success",
                "message": "点赞成功",
                "like_count": new_like_count
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[文章点赞错误] 点赞失败 - 文章ID: {article_id}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="点赞失败")

@router.post("/articles/search", response_model=Dict[str, Any])
async def search_articles(
    search_data: Dict[str, Any],
    current_user: SessionData = Depends(get_current_user)
):
    """
    搜索文章
    """
    try:
        keyword = search_data.get("keyword", "").strip()
        logger.info(f"[文章搜索] 搜索文章 - 关键词: {keyword}")
        
        if not keyword:
            return {
                "success": True,
                "results": [],
                "message": "请输入搜索关键词"
            }
        
        user_db = UserDatabase()
        
        with user_db._get_connection() as conn:
            cursor = conn.cursor()
            
            # 搜索文章
            search_term = f"%{keyword}%"
            cursor.execute("""
                SELECT id, title, content, author, category, created_at, view_count, like_count
                FROM articles 
                WHERE status = 'approved' AND (title LIKE ? OR content LIKE ?)
                ORDER BY created_at DESC
                LIMIT 50
            """, (search_term, search_term))
            
            articles = cursor.fetchall()
            
            # 格式化结果
            results = []
            for article in articles:
                results.append({
                    "id": article[0],
                    "title": article[1],
                    "content": article[2][:200] + "..." if len(article[2]) > 200 else article[2],
                    "author": article[3],
                    "category": article[4],
                    "created_at": article[5],
                    "view_count": article[6],
                    "like_count": article[7]
                })
            
            logger.info(f"[文章搜索成功] 找到 {len(results)} 篇文章")
            
            return {
                "success": True,
                "results": results,
                "message": f"找到 {len(results)} 篇相关文章"
            }
            
    except Exception as e:
        logger.error(f"[文章搜索错误] 搜索失败 - 关键词: {keyword}, 错误: {str(e)}", exc_info=True)
        return {
            "success": False,
            "results": [],
            "message": "搜索失败，请稍后重试"
        }

@router.get("/articles/categories/{category}", response_model=Dict[str, Any])
async def get_articles_by_category(category: str):
    """
    按分类获取文章
    """
    try:
        logger.info(f"[分类文章] 获取分类文章 - 分类: {category}")
        
        user_db = UserDatabase()
        
        with user_db._get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取该分类的文章
            cursor.execute("""
                SELECT id, title, content, author, category, created_at, view_count, like_count
                FROM articles 
                WHERE status = 'approved' AND category = ?
                ORDER BY created_at DESC
            """, (category,))
            
            articles = cursor.fetchall()
            
            # 格式化结果
            results = []
            for article in articles:
                results.append({
                    "id": article[0],
                    "title": article[1],
                    "content": article[2][:200] + "..." if len(article[2]) > 200 else article[2],
                    "author": article[3],
                    "category": article[4],
                    "created_at": article[5],
                    "view_count": article[6],
                    "like_count": article[7]
                })
            
            logger.info(f"[分类文章成功] 分类 {category} 有 {len(results)} 篇文章")
            
            return {
                "success": True,
                "articles": results,
                "category": category,
                "count": len(results)
            }
            
    except Exception as e:
        logger.error(f"[分类文章错误] 获取分类文章失败 - 分类: {category}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取分类文章失败")

@router.post("/articles/{article_id}/audit", response_model=Dict[str, Any])
async def audit_article(
    article_id: int,
    audit_data: Dict[str, Any],
    current_user: SessionData = Depends(get_current_user)
):
    """
    审核文章
    """
    try:
        status = audit_data.get("status", "").strip()
        logger.info(f"[文章审核] 审核文章 - 文章ID: {article_id}, 状态: {status}, 审核员: {current_user.username}")
        
        if status not in ["approved", "rejected"]:
            raise HTTPException(status_code=400, detail="无效的审核状态")
        
        user_db = UserDatabase()
        
        with user_db._get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查文章是否存在
            cursor.execute("SELECT id, title, author FROM articles WHERE id = ?", (article_id,))
            article = cursor.fetchone()
            
            if not article:
                raise HTTPException(status_code=404, detail="文章不存在")
            
            # 更新文章状态
            cursor.execute("""
                UPDATE articles 
                SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (status, article_id))
            
            conn.commit()
            
            logger.info(f"[文章审核成功] 文章 {article_id} 已{status} - 审核员: {current_user.username}")
            
            return {
                "success": True,
                "message": f"文章已{status}",
                "article_id": article_id,
                "status": status
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[文章审核错误] 审核文章失败 - 文章ID: {article_id}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="审核文章失败")

@router.get("/articles/{article_id}/complaints", response_model=Dict[str, Any])
async def get_article_complaints(
    article_id: int,
    current_user: SessionData = Depends(get_current_user)
):
    """
    获取文章的举报信息
    """
    try:
        logger.info(f"[文章举报] 获取文章举报信息 - 文章ID: {article_id}, 用户: {current_user.username}")
        
        user_db = UserDatabase()
        
        with user_db._get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查是否有complaints表，如果没有则创建
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS complaints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    reporter TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles (id)
                )
            """)
            
            # 获取文章的举报信息
            cursor.execute("""
                SELECT reporter, reason, created_at
                FROM complaints 
                WHERE article_id = ?
                ORDER BY created_at DESC
            """, (article_id,))
            
            complaints = cursor.fetchall()
            
            # 格式化结果
            results = []
            for complaint in complaints:
                results.append({
                    "reporter": complaint[0],
                    "reason": complaint[1],
                    "created_at": complaint[2]
                })
            
            logger.info(f"[文章举报成功] 文章 {article_id} 有 {len(results)} 条举报")
            
            return {
                "success": True,
                "complaints": results,
                "count": len(results)
            }
            
    except Exception as e:
        logger.error(f"[文章举报错误] 获取举报信息失败 - 文章ID: {article_id}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取举报信息失败")

@router.post("/articles/{article_id}/helpful", response_model=Dict[str, Any])
async def mark_article_helpful(
    article_id: int,
    current_user: SessionData = Depends(get_current_user)
):
    """
    标记文章为有帮助
    """
    try:
        logger.info(f"[文章有帮助] 用户标记文章有帮助 - 用户: {current_user.username}, 文章ID: {article_id}")
        
        user_db = UserDatabase()
        
        with user_db._get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查文章是否存在
            cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="文章不存在")
            
            # 增加有帮助数
            cursor.execute("UPDATE articles SET helpful_count = helpful_count + 1 WHERE id = ?", (article_id,))
            conn.commit()
            
            # 获取更新后的计数
            cursor.execute("SELECT helpful_count, unhelpful_count FROM articles WHERE id = ?", (article_id,))
            result = cursor.fetchone()
            new_helpful_count = result[0]
            new_unhelpful_count = result[1]
            
            logger.info(f"[文章有帮助成功] 文章ID: {article_id}, 新有帮助数: {new_helpful_count}")
            
            return {
                "status": "success",
                "message": "标记有帮助成功",
                "counts": {
                    "helpful_count": new_helpful_count,
                    "unhelpful_count": new_unhelpful_count
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[文章有帮助错误] 标记失败 - 文章ID: {article_id}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="标记有帮助失败")

@router.post("/articles/{article_id}/unhelpful", response_model=Dict[str, Any])
async def mark_article_unhelpful(
    article_id: int,
    current_user: SessionData = Depends(get_current_user)
):
    """
    标记文章为没帮助
    """
    try:
        logger.info(f"[文章没帮助] 用户标记文章没帮助 - 用户: {current_user.username}, 文章ID: {article_id}")
        
        user_db = UserDatabase()
        
        with user_db._get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查文章是否存在
            cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="文章不存在")
            
            # 增加没帮助数
            cursor.execute("UPDATE articles SET unhelpful_count = unhelpful_count + 1 WHERE id = ?", (article_id,))
            conn.commit()
            
            # 获取更新后的计数
            cursor.execute("SELECT helpful_count, unhelpful_count FROM articles WHERE id = ?", (article_id,))
            result = cursor.fetchone()
            new_helpful_count = result[0]
            new_unhelpful_count = result[1]
            
            logger.info(f"[文章没帮助成功] 文章ID: {article_id}, 新没帮助数: {new_unhelpful_count}")
            
            return {
                "status": "success",
                "message": "标记没帮助成功",
                "counts": {
                    "helpful_count": new_helpful_count,
                    "unhelpful_count": new_unhelpful_count
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[文章没帮助错误] 标记失败 - 文章ID: {article_id}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="标记没帮助失败")

# 添加别名以便在__init__.py中正确导入
article_router = router
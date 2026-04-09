from fastapi import APIRouter
from .auth_routes import auth_router
from .user_routes import user_router
from .article_routes import article_router
from .chat_routes import router as chat_router
from .psychology_routes import psychology_router
from .follow_routes import follow_router
from .comment_routes import comment_router
from .identity_routes import identity_router

# 创建主路由器
router = APIRouter()

# 包含所有子路由器
router.include_router(auth_router)
router.include_router(user_router)
router.include_router(article_router)
router.include_router(chat_router)
router.include_router(psychology_router)
router.include_router(follow_router)
router.include_router(comment_router)
router.include_router(identity_router)
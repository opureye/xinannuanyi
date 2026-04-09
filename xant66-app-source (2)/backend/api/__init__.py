# 导入所有路由模块
def get_combined_router():
    from fastapi import APIRouter
    from .auth_routes import auth_router
    from .user_routes import user_router
    from .admin_routes import admin_router
    from .article_routes import article_router
    from .chat_routes import router as chat_router
    
    # 创建主路由器
    main_router = APIRouter()
    
    # 包含所有子路由器
    main_router.include_router(auth_router)
    main_router.include_router(user_router)
    main_router.include_router(admin_router)
    main_router.include_router(article_router)
    main_router.include_router(chat_router)
    
    return main_router

# 创建默认路由器实例供外部导入
router = get_combined_router()
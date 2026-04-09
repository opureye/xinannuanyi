import time
import sys
import os
import logging
import json

# 获取当前文件的绝对路径
current_file = os.path.abspath(__file__)
# 获取backend目录的路径
backend_dir = os.path.dirname(current_file)
# 获取项目根目录的路径
root_dir = os.path.dirname(backend_dir)

# 将backend目录添加到Python路径，这样就可以直接导入api、utils等模块
sys.path.insert(0, backend_dir)
# 也将项目根目录添加到路径
sys.path.insert(0, root_dir)

# 打印路径信息用于调试
print(f"当前文件路径: {current_file}")
print(f"Backend目录: {backend_dir}")
print(f"项目根目录: {root_dir}")
print(f"Python路径: {sys.path}")

# 然后再导入其他模块
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import List, Dict, Optional
import backend.config as config_module
settings = config_module.settings

# 直接从backend包导入utils模块
import backend.utils.logger as logger_module
get_logger = logger_module.get_logger

# 配置日志
logger = get_logger(__name__)

# 现在再导入其他可能依赖路径设置的模块
try:
    import backend.utils.auth as auth_module
    get_current_user = auth_module.get_current_user
    require_role = auth_module.require_role
    from backend.api.routes import router as api_router
    from backend.api.admin_routes import admin_router
    from backend.api.ai_chat import router as ai_chat_router
    from backend.api.ai_chat import run_ai_chat, AIChatBody, ChatMessage, DEFAULT_MODEL as POLO_DEFAULT_MODEL
except ImportError as e:
    print(f"导入模块时出错: {e}")
    raise

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="信安暖驿——基于信息保护的医患交流分享平台（后端服务）"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins.split(','),
    allow_credentials=True,
    allow_methods=settings.cors_allow_methods.split(','),
    allow_headers=settings.cors_allow_headers.split(','),
)

# 注册API路由，添加/api前缀
app.include_router(api_router, prefix="/api")
# 注册管理员路由（添加/api前缀以保持一致性）
app.include_router(admin_router, prefix="/api")
# poloai 聊天转发：POST /api/ai/chat
app.include_router(ai_chat_router, prefix="/api")

# 在应用启动时初始化示例用户（只在首次启动时执行）
from backend.utils.database import initialize_sample_users_if_needed
initialize_sample_users_if_needed()

# 请求模型定义
class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = settings.default_model
    temperature: Optional[float] = settings.default_temperature
    max_tokens: Optional[int] = settings.default_max_tokens
    chat_history: Optional[List[Dict[str, str]]] = None
    api_key: Optional[str] = None  # 允许客户端提供API密钥（优先级高于服务器配置）

# 响应模型定义
class ChatResponse(BaseModel):
    response: str
    model: str
    token_usage: Optional[Dict[str, int]] = None
    timestamp: str

# 健康检查接口
@app.get("/health", tags=["系统"])
async def health_check():
    """检查服务健康状态"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version
    }

# 兼容旧客户端：与 /api/ai/chat 相同，统一走 poloai（backend.api.ai_chat.run_ai_chat）
@app.post("/api/generate", response_model=ChatResponse, tags=["对话"])
async def generate_response(request: ChatRequest):
    """生成AI对话响应（已改为与 /api/ai/chat 相同的上游转发）"""
    try:
        if not request.prompt.strip():
            raise HTTPException(status_code=400, detail="输入内容不能为空")

        model = request.model or POLO_DEFAULT_MODEL
        if model in ("deepseek-chat", "deepseek-coder", "deepseek-reasoner"):
            model = POLO_DEFAULT_MODEL

        messages_list: List[ChatMessage] = []
        if request.chat_history:
            for m in request.chat_history:
                if not isinstance(m, dict):
                    continue
                r = str(m.get("role", "")).lower()
                c = m.get("content")
                if c is None or not str(c).strip():
                    continue
                if r in ("user", "assistant", "system"):
                    messages_list.append(ChatMessage(role=r, content=str(c).strip()))
                elif r in ("使用者", "用户"):
                    messages_list.append(ChatMessage(role="user", content=str(c).strip()))
                elif r in ("管理员", "ai", "助手"):
                    messages_list.append(ChatMessage(role="assistant", content=str(c).strip()))
        messages_list.append(ChatMessage(role="user", content=request.prompt.strip()))

        body = AIChatBody(model=model, messages=messages_list)
        result = await run_ai_chat(body)
        content = ""
        try:
            content = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            pass
        if not content:
            raise HTTPException(status_code=502, detail="上游未返回有效回复内容")

        return {
            "response": content,
            "model": model,
            "token_usage": None,
            "timestamp": str(int(time.time())),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成响应失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成响应失败: {str(e)}")

# 配置前端静态文件服务
frontend_dir = os.path.join(root_dir, "frontend")
print(f"前端目录路径: {frontend_dir}")
print(f"前端目录是否存在: {os.path.exists(frontend_dir)}")

# 保留现有的根路径处理函数
@app.get("/")
async def read_root():
    """根路径重定向到登录页面"""
    login_file = os.path.join(frontend_dir, "4 login.html")
    if not os.path.exists(login_file):
        raise HTTPException(status_code=404, detail="登录页面不存在")
    return FileResponse(login_file)

css_dir = os.path.join(frontend_dir, "css")
print(f"CSS目录路径: {css_dir}")
print(f"CSS目录是否存在: {os.path.exists(css_dir)}")
if os.path.exists(css_dir):
    app.mount("/css", StaticFiles(directory=css_dir), name="css")

js_dir = os.path.join(frontend_dir, "js")
print(f"JS目录路径: {js_dir}")
print(f"JS目录是否存在: {os.path.exists(js_dir)}")
if os.path.exists(js_dir):
    app.mount("/js", StaticFiles(directory=js_dir), name="js")

images_dir = os.path.join(frontend_dir, "images")
print(f"Images目录路径: {images_dir}")
print(f"Images目录是否存在: {os.path.exists(images_dir)}")
if os.path.exists(images_dir):
    app.mount("/images", StaticFiles(directory=images_dir), name="images")

assets_dir = os.path.join(frontend_dir, "assets")
print(f"Assets目录路径: {assets_dir}")
print(f"Assets目录是否存在: {os.path.exists(assets_dir)}")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# 修改根路径静态文件服务的配置，移除html=True选项
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/hybridaction/zybTrackerStatisticsAction")
async def zyb_tracker_statistics_action(data: str = "", callback: str = Query(default="", alias="__callback__")):
    payload = {"success": True}
    if callback:
        return Response(content=f"{callback}({json.dumps(payload)})", media_type="application/javascript")
    return payload

# 主函数
if __name__ == "__main__":
    import uvicorn
    logger.info(f"启动{settings.app_name} v{settings.app_version}")
    logger.info(f"服务地址: http://{settings.host}:{settings.port}")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )

# 受保护页面路由 - 用户主页
@app.get("/me.html")
async def serve_me_page(_ = Depends(get_current_user)):
    """需要认证的用户主页"""
    me_file = os.path.join(frontend_dir, "1 me.html")
    if not os.path.exists(me_file):
        raise HTTPException(status_code=404, detail="用户主页不存在")
    return FileResponse(me_file)

# 受保护页面路由 - 管理员页面
@app.get("/audit_home.html")
async def serve_audit_page(_ = Depends(require_role("管理员"))):
    """需要管理员权限的审核页面"""
    audit_file = os.path.join(frontend_dir, "9 audit_home.html")
    if not os.path.exists(audit_file):
        raise HTTPException(status_code=404, detail="审核页面不存在")
    return FileResponse(audit_file)

# 在main.py末尾添加
# 处理带数字和空格的HTML文件请求
@app.get("/{filename}.html")
async def serve_html_file(filename: str):
    file_path = os.path.join(frontend_dir, f"{filename}.html")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="页面不存在")
    return FileResponse(file_path)

# 处理favicon.ico请求
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """提供网站图标"""
    # 使用正确的favicon.ico文件路径
    favicon_path = os.path.join(frontend_dir, "images", "favicon.ico")
    if not os.path.exists(favicon_path):
        # 如果找不到favicon.ico，尝试使用logo0.jpg作为备选
        alt_favicon_path = os.path.join(frontend_dir, "images", "logo0.jpg")
        if not os.path.exists(alt_favicon_path):
            raise HTTPException(status_code=404, detail="Favicon not found")
        favicon_path = alt_favicon_path
        
    # 为不同的文件类型设置正确的媒体类型
    if favicon_path.endswith('.ico'):
        media_type = 'image/x-icon'
    elif favicon_path.endswith('.jpg') or favicon_path.endswith('.jpeg'):
        media_type = 'image/jpeg'
    elif favicon_path.endswith('.png'):
        media_type = 'image/png'
    else:
        media_type = 'image/svg+xml'  # 默认媒体类型
        
    return FileResponse(
        favicon_path,
        media_type=media_type,
        filename="favicon.ico"  # 确保下载时使用正确的文件名
    )
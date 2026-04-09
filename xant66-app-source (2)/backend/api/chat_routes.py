# AI聊天相关的路由和功能
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
from typing import List, Dict, Any
import logging
from datetime import datetime
from .deepseek import DeepSeekAPI
from backend.config import get_settings, Settings
from .models import (
    Message,
    ChatCompletionRequest,
    GenerateRequest,
    GenerateResponse,
    ErrorResponse
)

# 创建路由实例
router = APIRouter(
    tags=["chat"]
)

# 配置日志
logger = logging.getLogger(__name__)

def get_deepseek_client(settings: Settings = Depends(get_settings)) -> DeepSeekAPI:
    """获取DeepSeek API客户端实例"""
    if not settings.deepseek_api_key:
        logger.error("DeepSeek API密钥未配置")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器未配置API密钥"
        )
    
    try:
        return DeepSeekAPI(
            api_key=settings.deepseek_api_key,
            timeout=settings.api_timeout,
            retry_count=settings.api_retry_count
        )
    except Exception as e:
        logger.error(f"创建DeepSeek API客户端失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="初始化API客户端失败"
        )

@router.post(
    "/chat/completions",
    response_model=Dict[str, Any],
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def chat_completions(
    request: ChatCompletionRequest,
    client: DeepSeekAPI = Depends(get_deepseek_client)
):
    """
    聊天补全接口，支持多轮对话
    """
    try:
        logger.info(f"接收聊天补全请求，模型: {request.model}，消息数量: {len(request.messages)}")
        
        # 转换消息格式
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # 调用DeepSeek API
        response = client.chat_completion(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream
        )
        
        return response
        
    except Exception as e:
        logger.error(f"聊天补全请求失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/generate",
    response_model=GenerateResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def generate(
    request: GenerateRequest,
    client: DeepSeekAPI = Depends(get_deepseek_client)
):
    """
    简单生成接口，根据单个提示生成响应
    """
    try:
        logger.info(f"接收生成请求，模型: {request.model}，提示长度: {len(request.prompt)}")
        
        # 调用DeepSeek API生成响应
        response_text = client.generate_response(
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # 获取当前时间戳
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        return {
            "response": response_text,
            "model": request.model,
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(f"生成请求失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/models",
    response_model=List[Dict[str, Any]],
    responses={
        500: {"model": ErrorResponse}
    }
)
async def get_models(client: DeepSeekAPI = Depends(get_deepseek_client)):
    """
    获取可用的模型列表
    """
    try:
        logger.info("获取模型列表请求")
        models = client.get_models()
        return models
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "ai-chat-api",
        "version": "1.0.0"
    }
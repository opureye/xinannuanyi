"""
poloai.top OpenAI 兼容聊天转发：与 api_reference_demo.py 保持同一域名、路径、请求头与模型字段。
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai-chat"])

settings = get_settings()
POLOAI_HOST = getattr(settings, "poloai_host", "https://poloai.top")
POLOAI_CHAT_PATH = "/v1/chat/completions"
DEFAULT_MODEL = "gpt-5-all"

# poloai.top API Key (从配置中读取)
POLOAI_AUTHORIZATION = getattr(settings, "poloai_api_key", "")


class ChatMessage(BaseModel):
    role: str = Field(..., description="user、assistant 或 system")
    content: str


class AIChatBody(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None


def _forward_to_poloai(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not POLOAI_AUTHORIZATION:
        raise HTTPException(status_code=503, detail="AI服务未配置API密钥，请联系管理员配置 POLOAI_API_KEY 环境变量")
    
    url = POLOAI_HOST.rstrip("/") + POLOAI_CHAT_PATH
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {POLOAI_AUTHORIZATION}",
        "Content-Type": "application/json",
    }
    logger.info(f"AI请求: {url}, 模型: {payload.get('model')}")
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
    except requests.RequestException as e:
        logger.exception("转发 poloai 请求失败")
        raise HTTPException(status_code=502, detail=f"上游网络错误: {e}") from e

    try:
        data = resp.json()
    except json.JSONDecodeError:
        text = resp.text[:2000]
        logger.error("poloai 返回非 JSON: %s", text)
        raise HTTPException(
            status_code=502,
            detail=f"上游返回非 JSON (HTTP {resp.status_code})",
        )

    if resp.status_code >= 400:
        detail = data.get("error") if isinstance(data, dict) else data
        # 将上游的401错误转换为502错误，避免前端误认为是用户认证失败
        if resp.status_code == 401:
            raise HTTPException(status_code=502, detail=f"上游认证失败: {detail}")
        raise HTTPException(status_code=resp.status_code, detail=detail)

    return data


async def run_ai_chat(body: AIChatBody) -> Dict[str, Any]:
    """
    供 /api/ai/chat 与 main.py 中 /api/generate 兼容层共用。
    """
    if not body.messages:
        raise HTTPException(status_code=400, detail="messages 不能为空")

    for m in body.messages:
        if not (m.content and str(m.content).strip()):
            raise HTTPException(status_code=400, detail="messages 中 content 不能为空")

    payload: Dict[str, Any] = {
        "model": body.model or DEFAULT_MODEL,
        "messages": [{"role": m.role, "content": m.content} for m in body.messages],
    }

    return await asyncio.to_thread(_forward_to_poloai, payload)


@router.post("/chat")
async def ai_chat(body: AIChatBody) -> Dict[str, Any]:
    """
    接收前端 messages 列表，转发至 https://poloai.top/v1/chat/completions
    """
    return await run_ai_chat(body)

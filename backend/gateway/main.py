"""
主 Agent 网关服务

支持两种部署模式：
1. 统一部署 (DEPLOY_MODE=unified): 所有服务在一个进程中运行
2. 分布式部署 (DEPLOY_MODE=distributed): 各服务独立运行，通过 A2A 协议通信

使用方式：
    # 统一部署（默认）
    python -m gateway.main

    # 分布式部署（需要先启动其他服务）
    DEPLOY_MODE=distributed python -m gateway.main
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.a2a import get_agent_card_json
from shared.server import build_fastapi_app

import copy
import json
import uuid
from typing import Optional

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types

from config import (
    API_HOST,
    GATEWAY_PORT,
    A2A_URLS,
    COFFEE_API_URL,
    DELIVERY_API_URL,
)

# A2A 相关导入
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# 创建根 Agent
from .agent import create_root_agent

# 配置
HOST = API_HOST
PORT = GATEWAY_PORT
APP_NAME = "gateway"
USER_ID = "default_user"
session_service = InMemorySessionService()

_root_agent = None


class ChatRequest(BaseModel):
    """聊天请求"""

    message: str
    session_id: Optional[str] = None


class CopilotKitMessage(BaseModel):
    """CopilotKit 消息"""

    role: str
    content: str


class CopilotKitRequest(BaseModel):
    """CopilotKit 请求"""

    messages: list[CopilotKitMessage]
    threadId: Optional[str] = None


# ==================== 辅助函数 ====================


def get_root_agent():
    """获取 root_agent"""
    global _root_agent
    if _root_agent is None:
        _root_agent = create_root_agent(A2A_URLS)
    return _root_agent


async def _fetch_store_info(store_id: str) -> dict:
    """通过 HTTP 调用获取门店信息"""
    try:
        client = await get_http_client()
        response = await client.get(f"{COFFEE_API_URL}/api/coffee/stores/{store_id}")
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {})
    except Exception:
        pass
    return {"name": "希希咖啡店", "address": "", "store_id": store_id}


async def _get_or_create_session(session_id: str, store_id: str):
    """获取或创建带有门店信息的 session"""
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session_id
    )
    if session is None:
        store_info = await _fetch_store_info(store_id)
        name = store_info.get("name", "希希咖啡店")
        address = store_info.get("address", "")
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
            state={
                "store_id": store_id,
                "store_name": name,
                "store_address": address,
                "store_display_name": f"{name}（{address}）" if address else name,
            },
        )
    return session


def serialize_event(event) -> dict:
    """序列化 ADK 事件为可 JSON 化的字典"""
    result = {"type": type(event).__name__}
    for attr in dir(event):
        if attr.startswith("_"):
            continue
        try:
            value = getattr(event, attr)
            if callable(value):
                continue
            if value is None:
                result[attr] = None
            elif isinstance(value, (str, int, float, bool)):
                result[attr] = value
            elif isinstance(value, (list, tuple)):
                result[attr] = [str(v) for v in value]
            elif isinstance(value, dict):
                result[attr] = {k: str(v) for k, v in value.items()}
            else:
                result[attr] = str(value)
        except:
            pass
    return result


def _format_state_value(value, indent: int = 0) -> str:
    """格式化单个 state 值，处理嵌套结构"""
    prefix = "  " * indent
    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = ["{"]
        for k, v in value.items():
            lines.append(f"{prefix}    {k}: {_format_state_value(v, indent + 1)}")
        lines.append(f"{prefix}  " + "}")
        return "\n".join(lines)
    if isinstance(value, list):
        if not value:
            return "[]"
        if len(value) <= 3 and all(isinstance(v, (str, int, float, bool)) for v in value):
            return f"[{', '.join(repr(v) for v in value)}]"
        return f"[{len(value)} items]"
    return repr(value)


def _log_session_state(state: dict, label: str, session_id: str = ""):
    """打印完整的 session state"""
    sid_short = session_id[:8] if session_id else "?"
    lines = [
        f"\n📋 ┌{'─' * 58}",
        f"📋 │ {label}  (session: {sid_short}…)",
        f"📋 ├{'─' * 58}",
    ]
    if not state:
        lines.append(f"📋 │   (empty)")
    else:
        for key in sorted(state.keys()):
            val = _format_state_value(state[key])
            if "\n" in val:
                lines.append(f"📋 │   {key}: {val.split(chr(10))[0]}")
                for sub in val.split("\n")[1:]:
                    lines.append(f"📋 │   {sub}")
            else:
                lines.append(f"📋 │   {key}: {val}")
    lines.append(f"📋 └{'─' * 58}\n")
    print("\n".join(lines), flush=True)


def _log_state_changes(prev: dict, curr: dict, trigger: str, session_id: str = ""):
    """对比并打印 state 变更（仅打印差异）"""
    all_keys = sorted(set(prev.keys()) | set(curr.keys()))
    changes = []
    for key in all_keys:
        old_val = prev.get(key)
        new_val = curr.get(key)
        if old_val != new_val:
            changes.append((key, old_val, new_val))
    if not changes:
        return
    sid_short = session_id[:8] if session_id else "?"
    lines = [
        f"\n🔄 ┌{'─' * 58}",
        f"🔄 │ State Changed  (session: {sid_short}…)",
        f"🔄 │ trigger: {trigger}",
        f"🔄 ├{'─' * 58}",
    ]
    for key, old_val, new_val in changes:
        if old_val is None:
            lines.append(f"🔄 │   + {key}: {_format_state_value(new_val)}")
        elif new_val is None:
            lines.append(f"🔄 │   - {key}: {_format_state_value(old_val)}")
        else:
            lines.append(f"🔄 │   ~ {key}:")
            lines.append(f"🔄 │       before: {_format_state_value(old_val)}")
            lines.append(f"🔄 │       after:  {_format_state_value(new_val)}")
    lines.append(f"🔄 └{'─' * 58}\n")
    print("\n".join(lines), flush=True)


async def lifespan(app: FastAPI):
    """应用生命周期"""
    global _root_agent
    _root_agent = create_root_agent(A2A_URLS)

    print(f"📡 API 转发配置:")
    print(f"   ☕ 咖啡店 API: {COFFEE_API_URL}")
    print(f"   🛵 配送 API: {DELIVERY_API_URL}")


app = build_fastapi_app(
    port=PORT,
    name="Buy A Coffee 网关服务",
    description="多 Agent 咖啡订购系统的主网关，整合所有服务",
    lifespan=lifespan,
)


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


@app.get("/api/health")
async def api_health():
    """API 健康检查"""
    return {
        "status": "healthy",
        "service": "gateway",
        "coffee_api": COFFEE_API_URL,
        "delivery_api": DELIVERY_API_URL,
    }


@app.get("/api/agents")
async def get_agents():
    """
    获取 A2A Agent 列表

    返回所有配置的 A2A Agent 信息，包括：
    - name: Agent 名称
    - description: Agent 描述
    - url: Agent Card URL
    - icon: Agent 图标（emoji）
    """
    agents = []

    # 从 A2A_URLS 配置中获取 Agent 信息
    for url in A2A_URLS:
        if not url or not url.strip():
            continue
        url = url.strip()

        # 尝试获取 Agent Card
        try:
            agent_card_url, card = await get_agent_card_json(url)
            agents.append(
                {
                    "name": card.get("name", "Unknown Agent"),
                    "description": card.get("description", ""),
                    "url": agent_card_url,
                    "icon": _get_agent_icon(card.get("name", "")),
                    "card": card,
                }
            )
        except Exception:
            pass
    return {"success": True, "agents": agents, "count": len(agents)}


# ==================== 门店端点 ====================


@app.get("/api/stores")
async def get_stores():
    """获取门店列表（转发到咖啡 API）"""
    client = await get_http_client()
    try:
        response = await client.get(f"{COFFEE_API_URL}/api/coffee/stores")
        return response.json()
    except Exception as e:
        return JSONResponse(
            status_code=502,
            content={"success": False, "error": f"获取门店列表失败: {str(e)}"},
        )


@app.get("/api/stores/{store_id}")
async def get_store(store_id: str):
    """获取门店详情（转发到咖啡 API）"""
    client = await get_http_client()
    try:
        response = await client.get(f"{COFFEE_API_URL}/api/coffee/stores/{store_id}")
        return response.json()
    except Exception as e:
        return JSONResponse(
            status_code=502,
            content={"success": False, "error": f"获取门店信息失败: {str(e)}"},
        )


def _get_agent_icon(name: str) -> str:
    """根据 Agent 名称返回对应的图标"""
    name_lower = name.lower()
    if "coffee" in name_lower or "咖啡" in name_lower:
        return "☕"
    elif "delivery" in name_lower or "配送" in name_lower:
        return "🛵"
    elif "assistant" in name_lower or "助手" in name_lower:
        return "🤖"
    elif "weather" in name_lower or "天气" in name_lower:
        return "🌤️"
    else:
        return "🤖"


def _extract_agent_name(url: str) -> str:
    """从 URL 中提取 Agent 名称"""
    # 移除协议和端口
    url = url.replace("http://", "").replace("https://", "")
    # 尝试从路径中提取名称
    parts = url.split("/")
    for part in parts:
        if part and part not in ["localhost", ".well-known", "agent.json"]:
            # 检查是否是端口号
            if not part.replace(":", "").isdigit():
                return part.replace("-", " ").replace("_", " ").title()
    return "Agent"


# ==================== API 转发 ====================
# 将 /api/coffee/* 和 /api/delivery/* 请求转发到对应的后端服务

# 创建异步 HTTP 客户端
_http_client: Optional[httpx.AsyncClient] = None


async def get_http_client() -> httpx.AsyncClient:
    """获取 HTTP 客户端单例"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


async def proxy_request(
    request: Request,
    target_base_url: str,
    path: str,
) -> Response:
    """
    转发请求到目标服务

    Args:
        request: 原始请求
        target_base_url: 目标服务的基础 URL
        path: 请求路径（不含前缀）

    Returns:
        转发后的响应
    """
    client = await get_http_client()

    # 构建目标 URL
    target_url = f"{target_base_url}{path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    # 获取请求体
    body = await request.body()

    # 构建请求头（排除 host）
    headers = dict(request.headers)
    headers.pop("host", None)

    try:
        # 发送请求
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
        )

        # 返回响应
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type"),
        )
    except httpx.RequestError as e:
        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "error": f"无法连接到后端服务: {str(e)}",
                "target_url": target_url,
            },
        )


@app.api_route(
    "/api/coffee/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_coffee_api(request: Request, path: str):
    """转发咖啡店 API 请求"""
    print(
        f"🔀 转发咖啡店 API: {request.method} /api/coffee/{path} -> {COFFEE_API_URL}/api/coffee/{path}"
    )
    return await proxy_request(request, COFFEE_API_URL, f"/api/coffee/{path}")


@app.api_route(
    "/api/delivery/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_delivery_api(request: Request, path: str):
    """转发配送 API 请求"""
    print(
        f"🔀 转发配送 API: {request.method} /api/delivery/{path} -> {DELIVERY_API_URL}/api/delivery/{path}"
    )
    return await proxy_request(request, DELIVERY_API_URL, f"/api/delivery/{path}")


# ==================== 聊天接口 ====================


@app.post("/api/chat")
async def chat(request: ChatRequest, req: Request):
    """非流式聊天"""
    store_id = req.headers.get("x-store-id", "store_001")
    session_id = request.session_id or str(uuid.uuid4())

    runner = Runner(
        agent=get_root_agent(),
        app_name=APP_NAME,
        session_service=session_service,
    )

    session = await _get_or_create_session(session_id, store_id)
    _log_session_state(dict(session.state), "Chat Start", session_id)
    prev_state = copy.deepcopy(dict(session.state))

    message = types.Content(
        role="user",
        parts=[types.Part(text=request.message)],
    )

    response_text = ""
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=message,
    ):
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    response_text += part.text

        curr_state = dict(session.state)
        if curr_state != prev_state:
            event_type = type(event).__name__
            _log_state_changes(prev_state, curr_state, event_type, session_id)
            prev_state = copy.deepcopy(curr_state)

    _log_session_state(dict(session.state), "Chat End", session_id)

    return {
        "success": True,
        "session_id": session_id,
        "response": response_text,
    }


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest, req: Request):
    """流式聊天（SSE）"""
    store_id = req.headers.get("x-store-id", "store_001")
    session_id = request.session_id or str(uuid.uuid4())

    runner = Runner(
        agent=get_root_agent(),
        app_name=APP_NAME,
        session_service=session_service,
    )

    session = await _get_or_create_session(session_id, store_id)
    _log_session_state(dict(session.state), "Chat Stream Start", session_id)
    prev_state_snapshot = copy.deepcopy(dict(session.state))

    message = types.Content(
        role="user",
        parts=[types.Part(text=request.message)],
    )

    run_config = RunConfig(
        streaming_mode=StreamingMode.SSE,
    )

    async def generate():
        """生成 SSE 事件"""
        nonlocal prev_state_snapshot

        yield {
            "event": "session",
            "data": json.dumps({"session_id": session_id}),
        }

        try:
            async for event in runner.run_async(
                user_id=USER_ID,
                session_id=session_id,
                new_message=message,
                run_config=run_config,
            ):
                event_type = type(event).__name__

                # 检测 state 变更
                curr_state = dict(session.state)
                if curr_state != prev_state_snapshot:
                    _log_state_changes(prev_state_snapshot, curr_state, event_type, session_id)
                    prev_state_snapshot = copy.deepcopy(curr_state)

                # 调试事件
                yield {
                    "event": "debug",
                    "data": json.dumps(
                        {
                            "event_type": event_type,
                            "event_data": serialize_event(event),
                        }
                    ),
                }

                # 文本响应
                is_partial = getattr(event, "partial", True)
                if hasattr(event, "content") and event.content:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            yield {
                                "event": "message",
                                "data": json.dumps(
                                    {
                                        "type": "text",
                                        "content": part.text,
                                        "partial": is_partial,
                                    }
                                ),
                            }
                        if hasattr(part, "function_call") and part.function_call:
                            fc = part.function_call
                            yield {
                                "event": "tool_call",
                                "data": json.dumps(
                                    {
                                        "type": "function_call",
                                        "name": (
                                            fc.name if hasattr(fc, "name") else str(fc)
                                        ),
                                        "args": fc.args if hasattr(fc, "args") else {},
                                        "id": fc.id if hasattr(fc, "id") else None,
                                    }
                                ),
                            }
                        if (
                            hasattr(part, "function_response")
                            and part.function_response
                        ):
                            fr = part.function_response
                            yield {
                                "event": "tool_result",
                                "data": json.dumps(
                                    {
                                        "type": "function_response",
                                        "name": (
                                            fr.name if hasattr(fr, "name") else str(fr)
                                        ),
                                        "response": (
                                            str(fr.response)
                                            if hasattr(fr, "response")
                                            else str(fr)
                                        ),
                                        "id": fr.id if hasattr(fr, "id") else None,
                                    }
                                ),
                            }

                # A2A 事件
                if "A2a" in event_type or "Remote" in event_type:
                    yield {
                        "event": "a2a",
                        "data": json.dumps(
                            {
                                "type": "a2a_event",
                                "event_type": event_type,
                                "details": serialize_event(event),
                            }
                        ),
                    }

        except Exception as e:
            import traceback

            yield {
                "event": "error",
                "data": json.dumps(
                    {
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                    }
                ),
            }

        _log_session_state(dict(session.state), "Chat Stream End", session_id)
        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(generate())


@app.post("/api/copilotkit")
async def copilotkit_chat(request: CopilotKitRequest, req: Request):
    """CopilotKit 兼容接口"""
    user_message = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            user_message = msg.content
            break

    if not user_message:
        return JSONResponse(
            status_code=400,
            content={"error": "No user message found"},
        )

    store_id = req.headers.get("x-store-id", "store_001")
    session_id = request.threadId or str(uuid.uuid4())

    runner = Runner(
        agent=get_root_agent(),
        app_name=APP_NAME,
        session_service=session_service,
    )

    await _get_or_create_session(session_id, store_id)

    message = types.Content(
        role="user",
        parts=[types.Part(text=user_message)],
    )

    response_text = ""
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=message,
    ):
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    response_text += part.text

    return {
        "threadId": session_id,
        "messages": [
            {"role": "assistant", "content": response_text},
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "gateway.main:app",
        host=HOST,
        port=PORT,
    )

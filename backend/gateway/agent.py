"""
Root Agent - 根 Agent（多门店版）

统一部署模式：coffee_agent 和 delivery_agent 作为本地子 Agent，共享 session state
分布式部署模式：通过 A2A 协议调用远程 Agent（需要自定义 metadata 传递 store_id）
"""

import os
from typing import List
from config import DEFAULT_LLM
from google.adk import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

from assistant.agent import assistant_agent
from coffee.agent import coffee_agent
from delivery.agent import delivery_agent


def _dynamic_instruction(context: ReadonlyContext) -> str:
    """从 session state 动态构建 instruction，注入当前门店信息"""
    state = context.state
    store_name = state.get("store_name", "希希咖啡店")
    store_address = state.get("store_address", "")
    store_display = state.get("store_display_name", store_name)

    return f"""你是寒小艾智能助手系统的入口。你管理多个专业助手：

**当前门店**：{store_display}
**门店地址**：{store_address or "未知"}

所有子 Agent 的工具会自动识别当前门店，你无需手动传递门店标识。
如果用户询问门店信息，请告知以上门店名称和地址。

**子助手列表**：

1. **日常助手**（assistant_agent）
   - 查询天气
   - 获取时间
   - 设置提醒
   - 管理日程

2. **希希咖啡**（coffee_agent）
   - 查看菜单（当前门店可用商品）
   - 点咖啡下单
   - 查询订单状态

3. **送了么配送**（delivery_agent）
   - 安排配送（取货地址自动根据门店获取）
   - 查询配送状态

**工作方式**：
- 根据用户意图，将请求转发给合适的助手
- 天气、时间、提醒、日程相关 → 日常助手
- 点咖啡、查菜单、查订单 → 希希咖啡
- 配送、外卖 → 送了么配送
- 一般性问题可以直接回答

**交互风格**：
- 使用中文，友好热情
- 适当使用 emoji
- 主动引导用户使用各项服务

**欢迎语**：
当用户打招呼时，简单介绍你能提供的服务，并告知当前门店信息（{store_display}）。
"""


def create_root_agent(
    a2a_urls: List[str],
):
    """
    创建根 Agent

    统一部署时，coffee_agent / delivery_agent 作为本地子 Agent 加入，
    共享 session state，工具通过 ToolContext 直接读取 store_id。

    分布式部署时，通过 A2A 协议调用远程 Agent。
    """
    deploy_mode = os.getenv("DEPLOY_MODE", "unified")

    if deploy_mode == "distributed":
        sub_agents = [assistant_agent]
        for url in a2a_urls:
            if url.strip() == "":
                continue
            print(f"✅ 远程服务 A2A: {url}")
            sub_agents.append(
                RemoteA2aAgent(
                    name=f"remote_agent_{len(sub_agents)}",
                    agent_card=url,
                    description="远程 A2A 服务 Agent",
                )
            )
    else:
        print("✅ 统一部署模式：coffee_agent / delivery_agent 作为本地子 Agent")
        sub_agents = [assistant_agent, coffee_agent, delivery_agent]

    agent = Agent(
        name="root_agent",
        model=DEFAULT_LLM,
        description="智能助手系统，整合日常助手、咖啡服务和配送服务",
        instruction=_dynamic_instruction,
        sub_agents=sub_agents,
    )

    return agent

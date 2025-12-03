"""
Root Agent - 根 Agent

通过 A2A 协议调用咖啡和配送服务
"""

from typing import List
from config import DEFAULT_LLM
from google.adk import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

# 导入本地助手 Agent（不通过 A2A）
from assistant.agent import assistant_agent


def create_root_agent(
    a2a_urls: List[str],
):
    """
    创建根 Agent（A2A 模式）

    Args:
        coffee_a2a_url: 咖啡服务 A2A Agent Card URL
        delivery_a2a_url: 配送服务 A2A Agent Card URL

    Returns:
        配置好的根 Agent
    """
    # 创建远程 A2A Agent

    a2a_agents = []
    for url in a2a_urls:
        if url.strip() == "":
            continue
        print(f"✅ 远程服务 A2A: {url}")

        a2a_agents.append(
            RemoteA2aAgent(
                name=f"remote_agent_{len(a2a_agents)+1}",
                agent_card=url,
                description="远程 A2A 服务 Agent",
            )
        )

    # print(f"✅ 咖啡服务 A2A: {coffee_a2a_url}")
    # print(f"✅ 配送服务 A2A: {delivery_a2a_url}")

    system_instruction = """你是寒小艾智能助手系统的入口。你管理三个专业助手：

1. **日常助手**（assistant_agent）
   - 查询天气
   - 获取时间
   - 设置提醒
   - 管理日程

2. **希希咖啡**- 通过 A2A 协议调用
   - 查看菜单
   - 点咖啡下单
   - 查询订单状态

3. **送了么配送**- 通过 A2A 协议调用
   - 安排配送
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
当用户打招呼时，简单介绍你能提供的服务。
"""

    agent = Agent(
        name="root_agent",
        model=DEFAULT_LLM,
        description="智能助手系统，整合日常助手、咖啡服务和配送服务",
        instruction=system_instruction,
        sub_agents=[assistant_agent, *a2a_agents],
    )

    return agent

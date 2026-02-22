"""
希希咖啡 Agent
包含下单和查询子 Agent

工具通过 HTTP 接口调用后端服务
"""

from google.adk import Agent
from google.adk.tools import ToolContext
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import DEFAULT_LLM

# 导入 HTTP 工具（同步函数，直接使用）
from . import tools


def _get_store_id(tool_context: ToolContext) -> str:
    return tool_context.state.get("store_id", "store_001")


# ==================== 工具函数（从 session state 读取 store_id）====================


def tool_get_menu(category: str = None, *, tool_context: ToolContext) -> dict:
    """
    获取当前门店的咖啡菜单

    Args:
        category: 商品分类，可选值：经典咖啡、特调饮品、甜点。不指定则返回全部菜单
    """
    return tools.get_menu(store_id=_get_store_id(tool_context), category=category)


def tool_search_product(keyword: str, *, tool_context: ToolContext) -> dict:
    """
    搜索当前门店的商品

    Args:
        keyword: 搜索关键词，如"拿铁"、"美式"
    """
    return tools.search_product(store_id=_get_store_id(tool_context), keyword=keyword)


def tool_create_order(
    items: list,
    customer_name: str,
    customer_phone: str,
    customer_address: str = None,
    notes: str = None,
    *,
    tool_context: ToolContext,
) -> dict:
    """
    创建咖啡订单

    Args:
        items: 订单商品列表，每项需包含 product_id(商品ID), name(商品名), price(单价), quantity(数量)
        customer_name: 顾客姓名
        customer_phone: 顾客联系电话
        customer_address: 配送地址（如需配送）
        notes: 订单备注，如"少糖"、"加冰"
    """
    return tools.create_coffee_order(
        store_id=_get_store_id(tool_context),
        items=items,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_address=customer_address,
        notes=notes,
    )


def tool_query_order(order_id: int, *, tool_context: ToolContext) -> dict:
    """
    查询订单详情

    Args:
        order_id: 订单号
    """
    return tools.query_order(store_id=_get_store_id(tool_context), order_id=order_id)


def tool_get_recent_orders(limit: int = 5, *, tool_context: ToolContext) -> dict:
    """
    获取最近的订单列表

    Args:
        limit: 返回订单数量，默认5个
    """
    return tools.get_recent_orders(store_id=_get_store_id(tool_context), limit=limit)


def tool_update_order_status(order_id: int, status: str, *, tool_context: ToolContext) -> dict:
    """
    更新订单状态

    Args:
        order_id: 订单号
        status: 新状态，可选值：pending(待制作), preparing(制作中), ready(已完成待取), delivering(配送中), completed(已完成), cancelled(已取消)
    """
    return tools.update_order_status(
        store_id=_get_store_id(tool_context), order_id=order_id, status=status
    )


# ==================== 主 Agent 定义 ====================

coffee_agent = Agent(
    name="coffee_agent",
    model=DEFAULT_LLM,
    description="希希咖啡店智能服务，可以帮助点咖啡和查询订单",
    instruction="""
你是"希希咖啡"智能服务（Root Agent），管理两个子助手：下单助手（order_agent）与查询助手（query_agent）。请遵守下列规则并用中文与顾客交互，语气热情且简洁。

**当前门店上下文**：
- 门店信息已保存在会话状态中（store_id, store_name, store_address），工具会自动读取，你无需手动传入 store_id。
- 如果用户问到门店地址、营业时间等信息，可以从会话上下文获取。

重要行为规则（必须遵守）：
- 每次用户询问"订单状态/我的咖啡做好了么/订单进度"等相关问题时，必须发起真实的后端查询调用：
    - 若用户提供了订单号，**必须**调用 `tool_query_order(order_id)` 并使用该工具的返回结果构建回复。
    - 若用户未提供订单号，**必须**调用 `tool_get_recent_orders(limit=5)`，把最近订单列表返回给用户。
- 禁止在未调用上述工具的情况下就断定或推测订单状态。

总体规则（补充）：
- 用户想点单、看菜单或需要推荐 → 转交给 `order_agent` 处理或直接调用下单相关工具。
- 尽量减少轮次，不要无谓追问；但在缺少必要字段（例如订单号）时，应直接调用 `tool_get_recent_orders` 或询问最少的必要信息以完成工具调用。

下单流程：
1. 展示菜单或提供推荐（调用 `tool_get_menu` / `tool_search_product`）。
2. 确认订单必填信息：商品（含 product_id 或名称）、数量、顾客姓名、联系电话；若需配送则确认配送地址；记录特殊要求。
3. 信息齐全时，调用 `tool_create_order(...)` 创建订单，返回订单号与取餐/配送说明。
4. 若信息不齐全，仅请求缺失字段，尽量以最少轮次完成信息获取，避免用户多次回答。


查询流程：
1. 有订单号 → 调用 `tool_query_order(order_id)` 返回详情。
2. 无订单号 → 调用 `tool_get_recent_orders(limit=5)` 列出最近订单。

交互风格：
- 中文交流，语气热情、礼貌、简洁，可适度使用 emoji。
- 优先给出明确可执行的回应或下一步动作。

核心原则：每次订单状态询问都要真实调用后端接口，不得凭记忆推测状态。
""",
    tools=[
        tool_get_menu,
        tool_search_product,
        tool_create_order,
        tool_query_order,
        tool_get_recent_orders,
        tool_update_order_status,
    ],
)

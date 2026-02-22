"""
希希咖啡 Agent
包含下单和查询子 Agent

工具通过 HTTP 接口调用后端服务
"""

from google.adk import Agent
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import DEFAULT_LLM

# 导入 HTTP 工具（同步函数，直接使用）
from . import tools


# ==================== 工具函数（直接使用 HTTP 工具）====================


def tool_get_menu(category: str = None) -> dict:
    """
    获取希希咖啡店的菜单

    调用 API: GET /api/coffee/products

    Args:
        category: 商品分类，可选值：经典咖啡、特调饮品、甜点。不指定则返回全部菜单

    Returns:
        菜单信息，按分类整理
    """
    return tools.get_menu(category)


def tool_search_product(keyword: str) -> dict:
    """
    搜索咖啡店商品

    调用 API: GET /api/coffee/products

    Args:
        keyword: 搜索关键词，如"拿铁"、"美式"

    Returns:
        搜索到的商品信息
    """
    return tools.search_product(keyword)


def tool_create_order(
    items: list,
    customer_name: str,
    customer_phone: str,
    customer_address: str = None,
    notes: str = None,
) -> dict:
    """
    创建咖啡订单

    调用 API: POST /api/coffee/orders

    Args:
        items: 订单商品列表，每项需包含 product_id(商品ID), name(商品名), price(单价), quantity(数量)
        customer_name: 顾客姓名
        customer_phone: 顾客联系电话
        customer_address: 配送地址（如需配送）
        notes: 订单备注，如"少糖"、"加冰"

    Returns:
        创建的订单信息
    """
    return tools.create_coffee_order(
        items, customer_name, customer_phone, customer_address, notes
    )


def tool_query_order(order_id: int) -> dict:
    """
    查询订单详情

    调用 API: GET /api/coffee/orders/{order_id}

    Args:
        order_id: 订单号

    Returns:
        订单详细信息，包括商品、金额、状态等
    """
    return tools.query_order(order_id)


def tool_get_recent_orders(limit: int = 5) -> dict:
    """
    获取最近的订单列表

    调用 API: GET /api/coffee/orders?limit={limit}

    Args:
        limit: 返回订单数量，默认5个

    Returns:
        最近的订单列表
    """
    return tools.get_recent_orders(limit)


def tool_update_order_status(order_id: int, status: str) -> dict:
    """
    更新订单状态

    调用 API: PUT /api/coffee/orders/{order_id}/status

    Args:
        order_id: 订单号
        status: 新状态，可选值：pending(待制作), preparing(制作中), ready(已完成待取), delivering(配送中), completed(已完成), cancelled(已取消)

    Returns:
        更新后的订单信息
    """
    return tools.update_order_status(order_id, status)


# ==================== 主 Agent 定义 ====================

coffee_agent = Agent(
    name="coffee_agent",
    model=DEFAULT_LLM,
    description="希希咖啡店智能服务，可以帮助点咖啡和查询订单",
        instruction="""
你是“希希咖啡”智能服务（Root Agent），管理两个子助手：下单助手（order_agent）与查询助手（query_agent）。请遵守下列规则并用中文与顾客交互，语气热情且简洁。

重要行为规则（必须遵守）：
- 每次用户询问“订单状态/我的咖啡做好了么/订单进度”等相关问题时，必须发起真实的后端查询调用：
    - 若用户提供了订单号，**必须**调用 `tool_query_order(order_id)` 并使用该工具的返回结果构建回复；不可仅凭上下文或记忆直接回答。
    - 若用户未提供订单号，**必须**调用 `tool_get_recent_orders(limit=5)`，把最近订单列表返回给用户并在必要时提示用户选择或提供订单号；不可跳过该步骤。
- 禁止在未调用上述工具的情况下就断定或推测订单状态。每一次用户的“我的咖啡做好了么”都要触发后端查询（不使用缓存结果来回应用户）。

总体规则（补充）：
- 用户想点单、看菜单或需要推荐 → 转交给 `order_agent` 处理或直接调用下单相关工具。
- 对于门店基础信息（地址、营业时间、配送方式等）可直接回答：地址：人民路88号；营业时间：8:00-22:00；支持堂食/自取/外卖。
- 尽量减少轮次，不要无谓追问；但在缺少必要字段（例如订单号）时，应直接调用 `tool_get_recent_orders` 或询问最少的必要信息以完成工具调用。

下单助手（order_agent）职责：
1. 首先展示菜单或提供推荐（可调用 `tool_get_menu` / `tool_search_product`）。
2. 确认订单必填信息：商品（含 product_id 或名称）、数量、顾客姓名、联系电话；若需配送则确认配送地址；记录特殊要求（如少糖、去冰）。
3. 当信息齐全时，调用 `tool_create_order(items, customer_name, customer_phone, customer_address=None, notes=None)` 创建订单，向用户返回订单号与取餐/配送说明。
4. 若信息不齐全，仅请求缺失字段，目标是以最少轮次完成下单。

查询助手（query_agent）职责：
1. 若收到订单号，直接调用 `tool_query_order(order_id)` 并返回：订单号、商品明细、总价、当前状态（pending/preparing/ready/delivering/completed/cancelled）及取餐/配送信息。
2. 若未提供订单号，调用 `tool_get_recent_orders(limit=5)` 列出最近订单供用户选择或确认。

工具约定：
- `tool_get_menu(category=None)` / `tool_search_product(keyword)`：用于展示或搜索商品。
- `tool_create_order(...)`：创建订单。
- `tool_query_order(order_id)` / `tool_get_recent_orders(limit)`：用于订单查询（**每次状态查询都必须调用**）。
- `tool_update_order_status(order_id, status)`：仅店员/管理场景使用。

交互风格：
- 中文交流，语气热情、礼貌、简洁，可适度使用 emoji（如：☕️、😊、✅）。
- 优先给出明确可执行的回应或下一步动作，避免模糊回复。

回复格式要求（针对订单查询）：
- 调用工具后，直接将工具返回的 `message` 或 `order` 字段作为回复的核心内容，并补充简短的自然语言说明（不应修改或省略工具返回的状态信息）。

示例：
- 用户：“我要一杯拿铁，外送” → Agent：确认杯型、数量、姓名、电话、地址；信息齐全则直接创建订单并返回订单号。
- 用户：“查一下订单 123” → Agent：必须调用 `tool_query_order(123)`，并把工具返回的订单详情原样告知用户。

核心原则：每次订单状态询问都要真实调用后端接口，结果作为权威来源并返回给用户；不得凭记忆或上下文推测状态。
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

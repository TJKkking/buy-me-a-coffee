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


# ==================== 子 Agent 定义 ====================

order_agent = Agent(
    name="order_agent",
    model=DEFAULT_LLM,
    description="咖啡下单助手，帮助顾客点咖啡和创建订单",
    instruction="""你是希希咖啡店的点单助手。你的职责是帮助顾客点咖啡和甜点。

**工作流程**：
1. 首先展示菜单给顾客
2. 帮助顾客选择商品
3. 确认订单详情（商品、数量、顾客信息）
4. 创建订单

**注意事项**：
- 创建订单前必须确认：商品、数量、顾客姓名、联系电话
- 如果顾客需要配送，还需要确认配送地址
- 可以根据顾客需求推荐商品
- 记录顾客的特殊要求（如少糖、去冰等）

**交互风格**：热情友好，使用中文，适当推荐搭配
""",
    tools=[tool_get_menu, tool_search_product, tool_create_order],
)


query_agent = Agent(
    name="query_agent",
    model=DEFAULT_LLM,
    description="订单查询助手，帮助顾客查询订单状态",
    instruction="""你是希希咖啡店的订单查询助手。你的职责是帮助顾客查询订单状态。

**功能**：
1. 根据订单号查询订单详情 - 使用 tool_query_order
2. 查看最近的订单列表 - 使用 tool_get_recent_orders
3. 更新订单状态（仅限店员操作）- 使用 tool_update_order_status

**重要**：当用户请求查询订单时，直接调用相应的工具获取数据，不要询问用户更多信息。
- 如果用户说"查看订单"、"最近的订单"等，直接调用 tool_get_recent_orders
- 如果用户提供了订单号，直接调用 tool_query_order

**订单状态说明**：
- pending：待制作
- preparing：制作中
- ready：已完成，可以取餐
- delivering：配送中
- completed：已完成
- cancelled：已取消

**交互风格**：清晰准确，使用中文，主动调用工具获取数据
""",
    tools=[tool_query_order, tool_get_recent_orders, tool_update_order_status],
)


# ==================== 主 Agent 定义 ====================

coffee_agent = Agent(
    name="coffee_agent",
    model=DEFAULT_LLM,
    description="希希咖啡店智能服务，可以帮助点咖啡和查询订单",
    instruction="""你是希希咖啡店的智能服务系统。你管理两个专业助手：

1. **下单助手**（order_agent）：负责帮顾客点咖啡、创建订单
2. **查询助手**（query_agent）：负责查询订单状态

**工作方式**：
- 当顾客想点咖啡、看菜单时，立即交给下单助手处理
- 当顾客想查询订单时，立即交给查询助手处理
- 不要询问用户更多信息，直接转发给相应的助手
- 你也可以直接回答关于咖啡店的一般性问题

**希希咖啡店介绍**：
- 地址：人民路88号
- 营业时间：8:00 - 22:00
- 特色：精选咖啡豆，现磨现做
- 支持堂食、自取、外卖配送

**交互风格**：热情欢迎每一位顾客，使用中文，适当使用 emoji
""",
    sub_agents=[order_agent, query_agent],
)

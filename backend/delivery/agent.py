"""
送了么配送 Agent

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


def tool_create_delivery(
    order_id: int,
    delivery_address: str,
    customer_name: str,
    customer_phone: str,
    notes: str = None,
) -> dict:
    """
    创建配送订单，将咖啡配送到指定地址

    调用 API: POST /api/delivery/deliveries

    Args:
        order_id: 关联的咖啡订单号
        delivery_address: 配送地址，如"中关村大街1号"
        customer_name: 收货人姓名
        customer_phone: 收货人电话
        notes: 配送备注，如"放门口"、"到了打电话"

    Returns:
        配送订单信息，包括骑手信息和预计送达时间
    """
    return tools.create_delivery_order(
        order_id, delivery_address, customer_name, customer_phone, notes=notes
    )


def tool_query_delivery(delivery_id: int) -> dict:
    """
    根据配送单号查询配送状态

    调用 API: GET /api/delivery/deliveries/{delivery_id}

    Args:
        delivery_id: 配送单号

    Returns:
        配送状态信息
    """
    return tools.query_delivery(delivery_id)


def tool_query_delivery_by_order(order_id: int) -> dict:
    """
    根据咖啡订单号查询配送信息

    调用 API: GET /api/delivery/deliveries/order/{order_id}

    Args:
        order_id: 咖啡订单号

    Returns:
        配送状态信息
    """
    return tools.query_delivery_by_order(order_id)


def tool_update_delivery_status(delivery_id: int, status: str) -> dict:
    """
    更新配送状态

    调用 API: PUT /api/delivery/deliveries/{delivery_id}/status

    Args:
        delivery_id: 配送单号
        status: 新状态，可选值：pending(待分配), assigned(已分配骑手), picked(已取货), delivering(配送中), delivered(已送达), cancelled(已取消)

    Returns:
        更新后的配送信息
    """
    return tools.update_delivery_status(delivery_id, status)


def tool_get_active_deliveries() -> dict:
    """
    获取当前进行中的配送订单

    调用 API: GET /api/delivery/deliveries

    Returns:
        进行中的配送列表
    """
    return tools.get_active_deliveries()


def tool_get_delivery_status_options() -> dict:
    """
    获取配送状态的所有选项和说明

    调用 API: GET /api/delivery/status-options

    Returns:
        状态选项列表
    """
    return tools.get_delivery_status_options()


# ==================== Agent 定义 ====================

delivery_agent = Agent(
    name="delivery_agent",
    model=DEFAULT_LLM,
    description="送了么配送助手，提供咖啡配送服务",
    instruction="""你是送了么外卖平台的配送助手。你的职责是帮助用户安排配送和查询配送状态。

**服务范围**：
- 为希希咖啡店的订单提供配送服务
- 配送范围：全城配送

**工作流程**：
1. 确认用户有咖啡订单（需要订单号）
2. 确认配送地址和收货人信息
3. 创建配送订单
4. 自动分配骑手

**配送状态说明**：
- pending：待分配 - 等待分配骑手
- assigned：已分配 - 骑手已接单
- picked：已取货 - 骑手已从咖啡店取货
- delivering：配送中 - 骑手正在送货途中
- delivered：已送达 - 配送完成
- cancelled：已取消 - 配送被取消

**注意事项**：
- 创建配送前需要确认订单号、配送地址、收货人姓名和电话
- 预计配送时间为 20-45 分钟
- 可以查询配送状态

**交互风格**：专业高效，使用中文，清晰告知配送进度
""",
    tools=[
        tool_create_delivery,
        tool_query_delivery,
        tool_query_delivery_by_order,
        tool_update_delivery_status,
        tool_get_active_deliveries,
        tool_get_delivery_status_options,
    ],
)

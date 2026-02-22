"""
送了么配送 Agent - 多门店版
工具通过 ToolContext 从 session state 获取 store_id
"""

from google.adk import Agent
from google.adk.tools import ToolContext
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import DEFAULT_LLM

from . import tools


def _get_store_id(tool_context: ToolContext) -> str:
    return tool_context.state.get("store_id", "store_001")


# ==================== 工具函数（从 session state 读取 store_id）====================


def tool_create_delivery(
    order_id: int,
    delivery_address: str,
    customer_name: str,
    customer_phone: str,
    notes: str = None,
    *,
    tool_context: ToolContext,
) -> dict:
    """
    创建配送订单，将咖啡配送到指定地址。取货地址会根据当前门店自动获取。

    Args:
        order_id: 关联的咖啡订单号
        delivery_address: 配送地址，如"中关村大街1号"
        customer_name: 收货人姓名
        customer_phone: 收货人电话
        notes: 配送备注，如"放门口"、"到了打电话"
    """
    return tools.create_delivery_order(
        store_id=_get_store_id(tool_context),
        order_id=order_id,
        delivery_address=delivery_address,
        customer_name=customer_name,
        customer_phone=customer_phone,
        notes=notes,
    )


def tool_query_delivery(delivery_id: int, *, tool_context: ToolContext) -> dict:
    """
    根据配送单号查询配送状态

    Args:
        delivery_id: 配送单号
    """
    return tools.query_delivery(
        store_id=_get_store_id(tool_context), delivery_id=delivery_id
    )


def tool_query_delivery_by_order(order_id: int, *, tool_context: ToolContext) -> dict:
    """
    根据咖啡订单号查询配送信息

    Args:
        order_id: 咖啡订单号
    """
    return tools.query_delivery_by_order(
        store_id=_get_store_id(tool_context), order_id=order_id
    )


def tool_update_delivery_status(delivery_id: int, status: str, *, tool_context: ToolContext) -> dict:
    """
    更新配送状态

    Args:
        delivery_id: 配送单号
        status: 新状态，可选值：pending(待分配), assigned(已分配骑手), picked(已取货), delivering(配送中), delivered(已送达), cancelled(已取消)
    """
    return tools.update_delivery_status(
        store_id=_get_store_id(tool_context), delivery_id=delivery_id, status=status
    )


def tool_get_active_deliveries(*, tool_context: ToolContext) -> dict:
    """
    获取当前门店进行中的配送订单
    """
    return tools.get_active_deliveries(store_id=_get_store_id(tool_context))


def tool_get_delivery_status_options() -> dict:
    """
    获取配送状态的所有选项和说明
    """
    return tools.get_delivery_status_options()


# ==================== Agent 定义 ====================

delivery_agent = Agent(
    name="delivery_agent",
    model=DEFAULT_LLM,
    description="送了么配送助手，提供咖啡配送服务",
    instruction="""你是送了么外卖平台的配送助手。你的职责是帮助用户安排配送和查询配送状态。

**当前门店上下文**：
- 门店信息已保存在会话状态中，工具会自动读取 store_id 并获取对应门店的取货地址。
- 你无需手动传入 store_id。

**服务范围**：
- 为希希咖啡店各门店的订单提供配送服务
- 配送范围：全城配送

**工作流程**：
1. 确认用户有咖啡订单（需要订单号）
2. 确认配送地址和收货人信息
3. 创建配送订单（取货地址自动根据门店获取）
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

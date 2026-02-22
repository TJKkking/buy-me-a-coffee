"""
配送相关工具 - 多门店版，通过 HTTP 接口调用后端服务
所有函数接受 store_id 参数，由 Agent wrapper 从 session state 注入。
"""
from typing import Optional
from shared.http_client import get_delivery_api_client, get_coffee_api_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DELIVERY_STATUS = {
    "pending": "待分配",
    "assigned": "已分配骑手",
    "picked": "已取货",
    "delivering": "配送中",
    "delivered": "已送达",
    "cancelled": "已取消",
}


def _store_headers(store_id: str) -> dict:
    return {"X-Store-Id": store_id}


def _get_pickup_address(store_id: str) -> str:
    """动态获取门店取货地址"""
    try:
        client = get_coffee_api_client()
        response = client.get(f"/api/coffee/stores/{store_id}")
        store = response.get("data", {})
        name = store.get("name", "希希咖啡店")
        address = store.get("address", "")
        return f"{name}（{address}）"
    except Exception:
        return "希希咖啡店"


def create_delivery_order(
    store_id: str,
    order_id: int,
    delivery_address: str,
    customer_name: str,
    customer_phone: str,
    pickup_address: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """
    创建配送订单

    Args:
        store_id: 门店ID
        order_id: 关联的咖啡订单号
        delivery_address: 配送地址
        customer_name: 收货人姓名
        customer_phone: 收货人电话
        pickup_address: 取货地址（不传则自动获取门店地址）
        notes: 配送备注
    """
    if not pickup_address:
        pickup_address = _get_pickup_address(store_id)

    client = get_delivery_api_client()

    try:
        response = client.post(
            "/api/delivery/deliveries",
            json={
                "order_id": order_id,
                "pickup_address": pickup_address,
                "delivery_address": delivery_address,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "notes": notes,
            },
            headers=_store_headers(store_id),
        )

        delivery = response.get("data", {})

        return {
            "success": True,
            "delivery": delivery,
            "message": f"配送订单已创建！\n配送单号：{delivery.get('id')}\n骑手：{delivery.get('driver_name')}（{delivery.get('driver_phone')}）\n预计 {delivery.get('estimated_time')} 分钟送达\n配送地址：{delivery_address}",
        }
    except Exception as e:
        return {"success": False, "delivery": None, "message": f"创建配送订单失败: {str(e)}"}


def query_delivery(store_id: str, delivery_id: int) -> dict:
    """
    查询配送状态

    Args:
        store_id: 门店ID
        delivery_id: 配送单号
    """
    client = get_delivery_api_client()

    try:
        response = client.get(
            f"/api/delivery/deliveries/{delivery_id}",
            headers=_store_headers(store_id),
        )
        delivery = response.get("data")

        if not delivery:
            return {"success": False, "delivery": None, "message": f"未找到配送单号 {delivery_id}"}

        status_text = DELIVERY_STATUS.get(delivery["status"], delivery["status"])

        return {
            "success": True,
            "delivery": delivery,
            "message": f"配送单 {delivery_id} 状态：{status_text}\n骑手：{delivery['driver_name']}\n配送地址：{delivery['delivery_address']}",
        }
    except Exception as e:
        return {"success": False, "delivery": None, "message": f"查询配送信息失败: {str(e)}"}


def query_delivery_by_order(store_id: str, order_id: int) -> dict:
    """
    根据咖啡订单号查询配送信息

    Args:
        store_id: 门店ID
        order_id: 咖啡订单号
    """
    client = get_delivery_api_client()

    try:
        response = client.get(
            f"/api/delivery/deliveries/order/{order_id}",
            headers=_store_headers(store_id),
        )
        delivery = response.get("data")

        if not delivery:
            return {
                "success": False,
                "delivery": None,
                "message": f"订单 {order_id} 暂无配送信息，可能是自取订单或尚未安排配送",
            }

        status_text = DELIVERY_STATUS.get(delivery["status"], delivery["status"])

        return {
            "success": True,
            "delivery": delivery,
            "message": f"订单 {order_id} 的配送信息：\n配送单号：{delivery['id']}\n状态：{status_text}\n骑手：{delivery['driver_name']}（{delivery['driver_phone']}）\n预计 {delivery['estimated_time']} 分钟送达",
        }
    except Exception as e:
        if "404" in str(e):
            return {
                "success": False,
                "delivery": None,
                "message": f"订单 {order_id} 暂无配送信息，可能是自取订单或尚未安排配送",
            }
        return {"success": False, "delivery": None, "message": f"查询配送信息失败: {str(e)}"}


def update_delivery_status(store_id: str, delivery_id: int, status: str) -> dict:
    """
    更新配送状态

    Args:
        store_id: 门店ID
        delivery_id: 配送单号
        status: 新状态
    """
    if status not in DELIVERY_STATUS:
        return {"success": False, "message": f"无效的状态值，可选：{list(DELIVERY_STATUS.keys())}"}

    client = get_delivery_api_client()

    try:
        response = client.put(
            f"/api/delivery/deliveries/{delivery_id}/status",
            json={"status": status},
            headers=_store_headers(store_id),
        )
        delivery = response.get("data")

        if not delivery:
            return {"success": False, "message": f"配送单 {delivery_id} 不存在"}

        return {
            "success": True,
            "delivery": delivery,
            "message": f"配送单 {delivery_id} 状态已更新为：{DELIVERY_STATUS[status]}",
        }
    except Exception as e:
        return {"success": False, "delivery": None, "message": f"更新配送状态失败: {str(e)}"}


def get_active_deliveries(store_id: str) -> dict:
    """
    获取门店进行中的配送订单

    Args:
        store_id: 门店ID
    """
    client = get_delivery_api_client()

    try:
        response = client.get("/api/delivery/deliveries", headers=_store_headers(store_id))
        all_deliveries = response.get("data", [])

        active = [
            d for d in all_deliveries if d["status"] not in ["delivered", "cancelled"]
        ]

        if not active:
            return {"success": True, "deliveries": [], "message": "当前没有进行中的配送"}

        simple_deliveries = []
        for d in active:
            simple_deliveries.append(
                {
                    "id": d["id"],
                    "order_id": d["order_id"],
                    "status": DELIVERY_STATUS.get(d["status"], d["status"]),
                    "driver": d["driver_name"],
                    "address": d["delivery_address"],
                    "estimated_time": d["estimated_time"],
                }
            )

        return {
            "success": True,
            "deliveries": simple_deliveries,
            "message": f"当前有 {len(active)} 个配送中的订单",
        }
    except Exception as e:
        return {"success": False, "deliveries": [], "message": f"获取配送列表失败: {str(e)}"}


def get_delivery_status_options() -> dict:
    """获取配送状态选项（不需要 store_id）"""
    return {
        "success": True,
        "status_options": DELIVERY_STATUS,
        "message": "配送状态说明",
    }

"""
配送相关工具 - 通过 HTTP 接口调用后端服务
"""
from typing import Optional
from shared.http_client import get_delivery_api_client
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 配送状态映射（用于显示）
DELIVERY_STATUS = {
    "pending": "待分配",
    "assigned": "已分配骑手",
    "picked": "已取货",
    "delivering": "配送中",
    "delivered": "已送达",
    "cancelled": "已取消",
}


def create_delivery_order(
    order_id: int,
    delivery_address: str,
    customer_name: str,
    customer_phone: str,
    pickup_address: str = "希希咖啡店（人民路88号）",
    notes: Optional[str] = None,
) -> dict:
    """
    创建配送订单
    
    通过 HTTP 调用: POST /api/delivery/deliveries

    Args:
        order_id: 关联的咖啡订单号
        delivery_address: 配送地址
        customer_name: 收货人姓名
        customer_phone: 收货人电话
        pickup_address: 取货地址（默认希希咖啡店）
        notes: 配送备注

    Returns:
        配送订单信息
    """
    client = get_delivery_api_client()
    
    try:
        response = client.post("/api/delivery/deliveries", json={
            "order_id": order_id,
            "pickup_address": pickup_address,
            "delivery_address": delivery_address,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "notes": notes,
        })
        
        delivery = response.get("data", {})

        return {
            "success": True,
            "delivery": delivery,
            "message": f"配送订单已创建！\n配送单号：{delivery.get('id')}\n骑手：{delivery.get('driver_name')}（{delivery.get('driver_phone')}）\n预计 {delivery.get('estimated_time')} 分钟送达\n配送地址：{delivery_address}",
        }
    except Exception as e:
        return {
            "success": False,
            "delivery": None,
            "message": f"创建配送订单失败: {str(e)}",
        }


def query_delivery(delivery_id: int) -> dict:
    """
    查询配送状态
    
    通过 HTTP 调用: GET /api/delivery/deliveries/{delivery_id}

    Args:
        delivery_id: 配送单号

    Returns:
        配送信息
    """
    client = get_delivery_api_client()
    
    try:
        response = client.get(f"/api/delivery/deliveries/{delivery_id}")
        delivery = response.get("data")

        if not delivery:
            return {
                "success": False,
                "delivery": None,
                "message": f"未找到配送单号 {delivery_id}",
            }

        status_text = DELIVERY_STATUS.get(delivery["status"], delivery["status"])

        return {
            "success": True,
            "delivery": delivery,
            "message": f"配送单 {delivery_id} 状态：{status_text}\n骑手：{delivery['driver_name']}\n配送地址：{delivery['delivery_address']}",
        }
    except Exception as e:
        return {
            "success": False,
            "delivery": None,
            "message": f"查询配送信息失败: {str(e)}",
        }


def query_delivery_by_order(order_id: int) -> dict:
    """
    根据咖啡订单号查询配送信息
    
    通过 HTTP 调用: GET /api/delivery/deliveries/order/{order_id}

    Args:
        order_id: 咖啡订单号

    Returns:
        配送信息
    """
    client = get_delivery_api_client()
    
    try:
        response = client.get(f"/api/delivery/deliveries/order/{order_id}")
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
        # 404 错误表示没有配送信息
        if "404" in str(e):
            return {
                "success": False,
                "delivery": None,
                "message": f"订单 {order_id} 暂无配送信息，可能是自取订单或尚未安排配送",
            }
        return {
            "success": False,
            "delivery": None,
            "message": f"查询配送信息失败: {str(e)}",
        }


def update_delivery_status(delivery_id: int, status: str) -> dict:
    """
    更新配送状态
    
    通过 HTTP 调用: PUT /api/delivery/deliveries/{delivery_id}/status

    Args:
        delivery_id: 配送单号
        status: 新状态

    Returns:
        更新结果
    """
    if status not in DELIVERY_STATUS:
        return {
            "success": False,
            "message": f"无效的状态值，可选：{list(DELIVERY_STATUS.keys())}",
        }

    client = get_delivery_api_client()
    
    try:
        response = client.put(f"/api/delivery/deliveries/{delivery_id}/status", json={"status": status})
        delivery = response.get("data")

        if not delivery:
            return {"success": False, "message": f"配送单 {delivery_id} 不存在"}

        return {
            "success": True,
            "delivery": delivery,
            "message": f"配送单 {delivery_id} 状态已更新为：{DELIVERY_STATUS[status]}",
        }
    except Exception as e:
        return {
            "success": False,
            "delivery": None,
            "message": f"更新配送状态失败: {str(e)}",
        }


def get_active_deliveries() -> dict:
    """
    获取进行中的配送订单
    
    通过 HTTP 调用: GET /api/delivery/deliveries

    Returns:
        配送列表
    """
    client = get_delivery_api_client()
    
    try:
        response = client.get("/api/delivery/deliveries")
        all_deliveries = response.get("data", [])
        
        # 过滤进行中的配送
        active = [
            d for d in all_deliveries if d["status"] not in ["delivered", "cancelled"]
        ]

        if not active:
            return {
                "success": True,
                "deliveries": [],
                "message": "当前没有进行中的配送",
            }

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
        return {
            "success": False,
            "deliveries": [],
            "message": f"获取配送列表失败: {str(e)}",
        }


def get_delivery_status_options() -> dict:
    """
    获取配送状态选项
    
    通过 HTTP 调用: GET /api/delivery/status-options

    Returns:
        状态选项
    """
    client = get_delivery_api_client()
    
    try:
        response = client.get("/api/delivery/status-options")
        return {
            "success": True,
            "status_options": response.get("data", DELIVERY_STATUS),
            "message": "配送状态说明",
        }
    except Exception as e:
        # 如果请求失败，返回本地定义的状态
        return {
            "success": True,
            "status_options": DELIVERY_STATUS,
            "message": "配送状态说明",
        }

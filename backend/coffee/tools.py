"""
咖啡相关工具 - 通过 HTTP 接口调用后端服务
"""
from typing import Optional
from shared.http_client import get_coffee_api_client
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_menu(category: Optional[str] = None) -> dict:
    """
    获取希希咖啡店菜单
    
    通过 HTTP 调用: GET /api/coffee/products

    Args:
        category: 商品分类（经典咖啡/特调饮品/甜点），不指定则返回全部

    Returns:
        菜单信息
    """
    logger.info(f"🔧 [TOOL] get_menu 被调用, category={category}")
    client = get_coffee_api_client()
    params = {"category": category} if category else None
    
    try:
        logger.info(f"🔧 [TOOL] 正在调用 HTTP: GET /api/coffee/products")
        response = client.get("/api/coffee/products", params=params)
        logger.info(f"🔧 [TOOL] HTTP 响应成功")
        products = response.get("data", [])
        
        # 按分类整理
        menu_by_category = {}
        for product in products:
            cat = product["category"]
            if cat not in menu_by_category:
                menu_by_category[cat] = []
            menu_by_category[cat].append(
                {
                    "id": product["id"],
                    "name": product["name"],
                    "price": product["price"],
                    "description": product["description"],
                    "icon": product.get("image_url", ""),
                }
            )

        return {
            "success": True,
            "menu": menu_by_category,
            "total_items": len(products),
            "message": "这是希希咖啡店的菜单，请问您想点什么？",
        }
    except Exception as e:
        logger.error(f"🔧 [TOOL] get_menu 失败: {str(e)}")
        return {
            "success": False,
            "menu": {},
            "message": f"获取菜单失败: {str(e)}",
        }


def search_product(keyword: str) -> dict:
    """
    搜索商品
    
    通过 HTTP 调用: GET /api/coffee/products 并过滤

    Args:
        keyword: 搜索关键词

    Returns:
        搜索结果
    """
    client = get_coffee_api_client()
    
    try:
        response = client.get("/api/coffee/products")
        products = response.get("data", [])
        
        # 在客户端进行关键词匹配
        keyword_lower = keyword.lower()
        matched = None
        for product in products:
            if keyword_lower in product["name"].lower() or keyword_lower in product.get("description", "").lower():
                matched = product
                break
        
        if matched:
            return {
                "success": True,
                "product": {
                    "id": matched["id"],
                    "name": matched["name"],
                    "price": matched["price"],
                    "description": matched["description"],
                    "category": matched["category"],
                },
                "message": f"找到了 {matched['name']}，价格 ¥{matched['price']}",
            }
        else:
            return {
                "success": False,
                "product": None,
                "message": f"抱歉，没有找到与 '{keyword}' 相关的商品",
            }
    except Exception as e:
        return {
            "success": False,
            "product": None,
            "message": f"搜索商品失败: {str(e)}",
        }


def create_coffee_order(
    items: list[dict],
    customer_name: str,
    customer_phone: str,
    customer_address: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """
    创建咖啡订单
    
    通过 HTTP 调用: POST /api/coffee/orders

    Args:
        items: 订单项列表，每项包含 product_id, name, price, quantity
        customer_name: 顾客姓名
        customer_phone: 顾客电话
        customer_address: 配送地址（可选，如果需要配送）
        notes: 备注

    Returns:
        订单信息
    """
    client = get_coffee_api_client()
    
    try:
        response = client.post("/api/coffee/orders", json={
            "items": items,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "customer_address": customer_address,
            "notes": notes,
        })
        
        order = response.get("data", {})
        
        # 格式化订单项
        items_text = "、".join([f"{item['name']}x{item['quantity']}" for item in items])

        return {
            "success": True,
            "order": order,
            "message": f"订单创建成功！\n订单号：{order.get('id')}\n商品：{items_text}\n总计：¥{order.get('total')}\n状态：待制作",
        }
    except Exception as e:
        return {
            "success": False,
            "order": None,
            "message": f"创建订单失败: {str(e)}",
        }


def query_order(order_id: int) -> dict:
    """
    查询订单状态
    
    通过 HTTP 调用: GET /api/coffee/orders/{order_id}

    Args:
        order_id: 订单号

    Returns:
        订单信息
    """
    client = get_coffee_api_client()
    
    try:
        response = client.get(f"/api/coffee/orders/{order_id}")
        order = response.get("data")
        
        if not order:
            return {
                "success": False,
                "order": None,
                "message": f"抱歉，未找到订单号为 {order_id} 的订单",
            }

        # 状态映射
        status_map = {
            "pending": "待制作",
            "preparing": "制作中",
            "ready": "已完成，待取餐",
            "delivering": "配送中",
            "completed": "已完成",
            "cancelled": "已取消",
        }

        status_text = status_map.get(order["status"], order["status"])
        items_text = "、".join(
            [f"{item['name']}x{item['quantity']}" for item in order.get("items", [])]
        )

        return {
            "success": True,
            "order": order,
            "message": f"订单 {order_id} 信息：\n商品：{items_text}\n总计：¥{order['total']}\n状态：{status_text}\n下单时间：{order['created_at']}",
        }
    except Exception as e:
        return {
            "success": False,
            "order": None,
            "message": f"查询订单失败: {str(e)}",
        }


def get_recent_orders(limit: int = 5) -> dict:
    """
    获取最近的订单
    
    通过 HTTP 调用: GET /api/coffee/orders?limit={limit}

    Args:
        limit: 返回数量

    Returns:
        订单列表
    """
    logger.info(f"🔧 [TOOL] get_recent_orders 被调用, limit={limit}")
    client = get_coffee_api_client()
    
    try:
        logger.info(f"🔧 [TOOL] 正在调用 HTTP: GET /api/coffee/orders?limit={limit}")
        response = client.get("/api/coffee/orders", params={"limit": limit})
        logger.info(f"🔧 [TOOL] HTTP 响应成功")
        orders = response.get("data", [])

        if not orders:
            return {"success": True, "orders": [], "message": "暂无订单记录"}

        # 简化订单信息
        simple_orders = []
        for order in orders:
            items_text = "、".join(
                [f"{item['name']}x{item['quantity']}" for item in order.get("items", [])]
            )
            simple_orders.append(
                {
                    "id": order["id"],
                    "items": items_text,
                    "total": order["total"],
                    "status": order["status"],
                    "created_at": order["created_at"],
                }
            )

        return {
            "success": True,
            "orders": simple_orders,
            "message": f"最近 {len(orders)} 个订单",
        }
    except Exception as e:
        return {
            "success": False,
            "orders": [],
            "message": f"获取订单列表失败: {str(e)}",
        }


def update_order_status(order_id: int, status: str) -> dict:
    """
    更新订单状态
    
    通过 HTTP 调用: PUT /api/coffee/orders/{order_id}/status

    Args:
        order_id: 订单号
        status: 新状态

    Returns:
        更新结果
    """
    client = get_coffee_api_client()
    
    try:
        response = client.put(f"/api/coffee/orders/{order_id}/status", json={"status": status})
        order = response.get("data")

        if not order:
            return {"success": False, "message": f"订单 {order_id} 不存在"}

        status_map = {
            "pending": "待制作",
            "preparing": "制作中",
            "ready": "已完成，待取餐",
            "delivering": "配送中",
            "completed": "已完成",
            "cancelled": "已取消",
        }

        return {
            "success": True,
            "order": order,
            "message": f"订单 {order_id} 状态已更新为：{status_map.get(status, status)}",
        }
    except Exception as e:
        return {
            "success": False,
            "order": None,
            "message": f"更新订单状态失败: {str(e)}",
        }

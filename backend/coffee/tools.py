"""
咖啡相关工具 - 多门店版，通过 HTTP 接口调用后端服务
所有函数接受 store_id 参数，由 Agent wrapper 从 session state 注入。
"""
import re
import time
from typing import Any, Dict, List, Optional
from shared.http_client import get_coffee_api_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_PRODUCT_CACHE: Dict[str, Dict[str, Any]] = {}
_PRODUCT_CACHE_TTL = 60


def _store_headers(store_id: str) -> dict:
    return {"X-Store-Id": store_id}


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", value).lower()


def _safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
    if isinstance(value, str):
        match = re.search(r"\d+", value)
        if match:
            try:
                return int(match.group())
            except ValueError:
                return default
    return default


def _parse_price(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = re.sub(r"[^\d.]", "", value)
        if cleaned:
            try:
                return float(cleaned)
            except ValueError:
                return None
    return None


def _extract_name_and_quantity(raw: str) -> tuple[str, int]:
    text = raw.strip()
    quantity = 1

    match = re.search(r"(.+?)[x×＊*](\d+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip(), int(match.group(2))

    match = re.search(r"(.+?)(\d+)\s*(杯|份|个|杯子|shot)?$", text)
    if match:
        return match.group(1).strip(), int(match.group(2))

    return text, quantity


def _get_product_catalog(store_id: str) -> List[Dict[str, Any]]:
    """获取门店菜单缓存（per-store）"""
    now = time.time()
    cache = _PRODUCT_CACHE.get(store_id, {"expires_at": 0.0, "items": []})
    if now >= cache["expires_at"]:
        client = get_coffee_api_client()
        logger.info(f"🔧 [TOOL] 刷新门店 {store_id} 商品缓存")
        response = client.get("/api/coffee/products", headers=_store_headers(store_id))
        cache = {
            "items": response.get("data", []),
            "expires_at": now + _PRODUCT_CACHE_TTL,
        }
        _PRODUCT_CACHE[store_id] = cache
    return cache["items"]


def _find_product_by_name(name: str, catalog: List[Dict[str, Any]]):
    normalized = _normalize_text(name)
    for product in catalog:
        if _normalize_text(product["name"]) == normalized:
            return product
    for product in catalog:
        if normalized in _normalize_text(product["name"]):
            return product
    return None


def _normalize_order_items(store_id: str, items: list) -> List[Dict[str, Any]]:
    """清洗并补全订单项数据"""
    if not isinstance(items, list) or len(items) == 0:
        raise ValueError("订单至少需要包含一件商品。")

    catalog = _get_product_catalog(store_id)
    normalized_items: List[Dict[str, Any]] = []

    for raw_item in items:
        if isinstance(raw_item, dict):
            item = raw_item.copy()
            name = item.get("name") or item.get("product_name") or item.get("title")
            product_id = (
                item.get("product_id")
                or item.get("productId")
                or item.get("id")
            )
            quantity = (
                item.get("quantity")
                or item.get("qty")
                or item.get("count")
                or item.get("num")
                or 1
            )
            price = item.get("price") or item.get("amount")
        elif isinstance(raw_item, str):
            name, quantity = _extract_name_and_quantity(raw_item)
            product_id = None
            price = None
        else:
            raise ValueError("无法解析的商品格式，请重新确认点单信息。")

        product_id = _safe_int(product_id)
        quantity = max(1, _safe_int(quantity, default=1))
        price_value = _parse_price(price)

        matched_product = None
        if product_id is not None:
            matched_product = next(
                (p for p in catalog if int(p["id"]) == product_id),
                None,
            )

        if not matched_product and name:
            matched_product = _find_product_by_name(name, catalog)
            if matched_product:
                product_id = int(matched_product["id"])
                name = matched_product["name"]

        if not matched_product:
            raise ValueError(f"未找到商品 {name or product_id}，请重新选择菜单中的商品。")

        if price_value is None:
            price_value = matched_product["price"]
        else:
            price_value = float(price_value)

        normalized_items.append(
            {
                "product_id": int(product_id),
                "name": name or matched_product["name"],
                "price": price_value,
                "quantity": int(quantity),
            }
        )

    return normalized_items


# ==================== 公开工具函数 ====================


def get_menu(store_id: str, category: Optional[str] = None) -> dict:
    """
    获取门店菜单

    Args:
        store_id: 门店ID
        category: 商品分类
    """
    logger.info(f"🔧 [TOOL] get_menu 被调用, store_id={store_id}, category={category}")
    client = get_coffee_api_client()
    params = {"category": category} if category else None

    try:
        response = client.get("/api/coffee/products", params=params, headers=_store_headers(store_id))
        products = response.get("data", [])

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
            "message": "这是本店的菜单，请问您想点什么？",
        }
    except Exception as e:
        logger.error(f"🔧 [TOOL] get_menu 失败: {str(e)}")
        return {"success": False, "menu": {}, "message": f"获取菜单失败: {str(e)}"}


def search_product(store_id: str, keyword: str) -> dict:
    """
    搜索门店商品

    Args:
        store_id: 门店ID
        keyword: 搜索关键词
    """
    client = get_coffee_api_client()

    try:
        response = client.get("/api/coffee/products", headers=_store_headers(store_id))
        products = response.get("data", [])

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
        return {"success": False, "product": None, "message": f"搜索商品失败: {str(e)}"}


def create_coffee_order(
    store_id: str,
    items: list[dict],
    customer_name: str,
    customer_phone: str,
    customer_address: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """
    创建咖啡订单

    Args:
        store_id: 门店ID
        items: 订单项列表
        customer_name: 顾客姓名
        customer_phone: 顾客电话
        customer_address: 配送地址
        notes: 备注
    """
    client = get_coffee_api_client()

    try:
        normalized_items = _normalize_order_items(store_id, items)
        logger.info(f"🔧 [TOOL] create_coffee_order 规范化订单项: {normalized_items}")

        response = client.post(
            "/api/coffee/orders",
            json={
                "items": normalized_items,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "customer_address": customer_address,
                "notes": notes,
            },
            headers=_store_headers(store_id),
        )

        order = response.get("data", {})
        items_text = "、".join(
            [f"{item['name']}x{item['quantity']}" for item in normalized_items]
        )

        return {
            "success": True,
            "order": order,
            "message": f"订单创建成功！\n订单号：{order.get('id')}\n商品：{items_text}\n总计：¥{order.get('total')}\n状态：待制作",
        }
    except Exception as e:
        return {"success": False, "order": None, "message": f"创建订单失败: {str(e)}"}


def query_order(store_id: str, order_id: int) -> dict:
    """
    查询订单状态

    Args:
        store_id: 门店ID
        order_id: 订单号
    """
    client = get_coffee_api_client()

    try:
        response = client.get(f"/api/coffee/orders/{order_id}", headers=_store_headers(store_id))
        order = response.get("data")

        if not order:
            return {
                "success": False,
                "order": None,
                "message": f"抱歉，未找到订单号为 {order_id} 的订单",
            }

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
        return {"success": False, "order": None, "message": f"查询订单失败: {str(e)}"}


def get_recent_orders(store_id: str, limit: int = 5) -> dict:
    """
    获取门店最近订单

    Args:
        store_id: 门店ID
        limit: 返回数量
    """
    logger.info(f"🔧 [TOOL] get_recent_orders 被调用, store_id={store_id}, limit={limit}")
    client = get_coffee_api_client()

    try:
        response = client.get("/api/coffee/orders", params={"limit": limit}, headers=_store_headers(store_id))
        orders = response.get("data", [])

        if not orders:
            return {"success": True, "orders": [], "message": "暂无订单记录"}

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
        return {"success": False, "orders": [], "message": f"获取订单列表失败: {str(e)}"}


def update_order_status(store_id: str, order_id: int, status: str) -> dict:
    """
    更新订单状态

    Args:
        store_id: 门店ID
        order_id: 订单号
        status: 新状态
    """
    client = get_coffee_api_client()

    try:
        response = client.put(
            f"/api/coffee/orders/{order_id}/status",
            json={"status": status},
            headers=_store_headers(store_id),
        )
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
        return {"success": False, "order": None, "message": f"更新订单状态失败: {str(e)}"}


def get_store_info(store_id: str) -> dict:
    """
    获取门店详情

    Args:
        store_id: 门店ID
    """
    client = get_coffee_api_client()

    try:
        response = client.get(f"/api/coffee/stores/{store_id}")
        store = response.get("data")
        if not store:
            return {"success": False, "message": f"门店 {store_id} 不存在"}
        return {
            "success": True,
            "store": store,
            "display_name": f"{store['name']}（{store['address']}）",
            "message": f"门店信息：{store['name']}（{store['address']}），营业时间 {store.get('business_hours', '')}",
        }
    except Exception as e:
        return {"success": False, "message": f"获取门店信息失败: {str(e)}"}

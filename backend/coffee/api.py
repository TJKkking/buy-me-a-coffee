"""
希希咖啡店 REST API - 多门店版
"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from .database import coffee_db

router = APIRouter(tags=["希希咖啡"])


class OrderItem(BaseModel):
    product_id: int
    name: str
    price: float
    quantity: int


class CreateOrderRequest(BaseModel):
    items: list[OrderItem]
    customer_name: str
    customer_phone: str
    customer_address: Optional[str] = None
    notes: Optional[str] = None


class UpdateOrderStatusRequest(BaseModel):
    status: str


class UpdateAvailabilityRequest(BaseModel):
    available: int
    stock: Optional[int] = None


# ==================== 门店端点 ====================


@router.get("/stores")
async def get_stores():
    """获取所有门店列表"""
    stores = await coffee_db.get_stores()
    return {"success": True, "data": stores, "message": "获取门店列表成功"}


@router.get("/stores/{store_id}")
async def get_store(store_id: str):
    """获取门店详情"""
    store = await coffee_db.get_store(store_id)
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    return {"success": True, "data": store, "message": "获取门店详情成功"}


# ==================== 商品端点 ====================


@router.get("/products")
async def get_products(
    category: Optional[str] = None,
    x_store_id: str = Header(..., alias="X-Store-Id"),
):
    """获取门店商品列表"""
    products = await coffee_db.get_products(store_id=x_store_id, category=category)
    return {"success": True, "data": products, "message": "获取商品列表成功"}


@router.get("/products/{product_id}")
async def get_product(product_id: int):
    """获取商品详情（全局共享菜单）"""
    product = await coffee_db.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return {"success": True, "data": product, "message": "获取商品详情成功"}


# ==================== 订单端点 ====================


@router.post("/orders")
async def create_order(
    request: CreateOrderRequest,
    x_store_id: str = Header(..., alias="X-Store-Id"),
):
    """创建订单"""
    items = [item.model_dump() for item in request.items]
    order = await coffee_db.create_order(
        store_id=x_store_id,
        items=items,
        customer_name=request.customer_name,
        customer_phone=request.customer_phone,
        customer_address=request.customer_address,
        notes=request.notes,
    )
    return {
        "success": True,
        "data": order,
        "message": f"订单创建成功，订单号：{order['id']}",
    }


@router.get("/orders")
async def get_orders(
    status: Optional[str] = None,
    limit: int = 50,
    x_store_id: str = Header(..., alias="X-Store-Id"),
):
    """获取门店订单列表"""
    orders = await coffee_db.get_orders(store_id=x_store_id, status=status, limit=limit)
    return {"success": True, "data": orders, "message": "获取订单列表成功"}


@router.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    x_store_id: str = Header(..., alias="X-Store-Id"),
):
    """获取订单详情"""
    order = await coffee_db.get_order(order_id, store_id=x_store_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return {"success": True, "data": order, "message": "获取订单详情成功"}


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    request: UpdateOrderStatusRequest,
    x_store_id: str = Header(..., alias="X-Store-Id"),
):
    """更新订单状态"""
    order = await coffee_db.update_order_status(order_id, request.status, store_id=x_store_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return {
        "success": True,
        "data": order,
        "message": f"订单状态已更新为：{request.status}",
    }


@router.get("/categories")
async def get_categories(
    x_store_id: str = Header(..., alias="X-Store-Id"),
):
    """获取门店可用商品分类"""
    products = await coffee_db.get_products(store_id=x_store_id)
    categories = list(set(p["category"] for p in products))
    return {"success": True, "data": categories, "message": "获取分类成功"}


# ==================== 管理端预留端点 ====================


@router.put("/stores/{store_id}/products/{product_id}/availability")
async def update_product_availability(
    store_id: str,
    product_id: int,
    request: UpdateAvailabilityRequest,
):
    """设置门店商品可用状态（沽清/恢复）"""
    result = await coffee_db.update_product_availability(
        store_id=store_id,
        product_id=product_id,
        available=request.available,
        stock=request.stock,
    )
    if not result:
        raise HTTPException(status_code=404, detail="商品不存在")
    action = "恢复上架" if request.available else "沽清"
    return {
        "success": True,
        "data": result,
        "message": f"商品已{action}",
    }


@router.get("/stores/{store_id}/stats")
async def get_store_stats(store_id: str):
    """获取门店经营统计"""
    stats = await coffee_db.get_store_stats(store_id)
    return {"success": True, "data": stats, "message": "获取门店统计成功"}

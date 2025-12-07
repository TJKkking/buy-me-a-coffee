"""
希希咖啡店 REST API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from .database import coffee_db

router = APIRouter(tags=["希希咖啡"])


class OrderItem(BaseModel):
    """订单项"""
    product_id: int
    name: str
    price: float
    quantity: int


class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    items: list[OrderItem]
    customer_name: str
    customer_phone: str
    customer_address: Optional[str] = None
    notes: Optional[str] = None


class UpdateOrderStatusRequest(BaseModel):
    """更新订单状态请求"""
    status: str


@router.get("/products")
async def get_products(category: Optional[str] = None):
    """获取商品列表"""
    products = await coffee_db.get_products(category)
    return {"success": True, "data": products, "message": "获取商品列表成功"}


@router.get("/products/{product_id}")
async def get_product(product_id: int):
    """获取商品详情"""
    product = await coffee_db.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return {"success": True, "data": product, "message": "获取商品详情成功"}


@router.post("/orders")
async def create_order(request: CreateOrderRequest):
    """创建订单"""
    print(0000)
    items = [item.model_dump() for item in request.items]
    print(1234)
    order = await coffee_db.create_order(
        items=items,
        customer_name=request.customer_name,
        customer_phone=request.customer_phone,
        customer_address=request.customer_address,
        notes=request.notes,
    )
    print(7890)
    print(order)

    return {
        "success": True,
        "data": order,
        "message": f"订单创建成功，订单号：{order['id']}",
    }


@router.get("/orders")
async def get_orders(status: Optional[str] = None, limit: int = 50):
    """获取订单列表"""
    orders = await coffee_db.get_orders(status, limit)
    return {"success": True, "data": orders, "message": "获取订单列表成功"}


@router.get("/orders/{order_id}")
async def get_order(order_id: int):
    """获取订单详情"""
    order = await coffee_db.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return {"success": True, "data": order, "message": "获取订单详情成功"}


@router.put("/orders/{order_id}/status")
async def update_order_status(order_id: int, request: UpdateOrderStatusRequest):
    """更新订单状态"""
    order = await coffee_db.update_order_status(order_id, request.status)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return {
        "success": True,
        "data": order,
        "message": f"订单状态已更新为：{request.status}",
    }


@router.get("/categories")
async def get_categories():
    """获取商品分类"""
    products = await coffee_db.get_products()
    categories = list(set(p["category"] for p in products))
    return {"success": True, "data": categories, "message": "获取分类成功"}


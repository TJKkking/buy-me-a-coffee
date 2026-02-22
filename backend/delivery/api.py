"""
送了么配送 REST API - 多门店版
"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from .database import delivery_db, DELIVERY_STATUS

router = APIRouter(tags=["送了么配送"])


class CreateDeliveryRequest(BaseModel):
    order_id: int
    pickup_address: str
    delivery_address: str
    customer_name: str
    customer_phone: str
    notes: Optional[str] = None


class UpdateDeliveryStatusRequest(BaseModel):
    status: str


@router.post("/deliveries")
async def create_delivery(
    request: CreateDeliveryRequest,
    x_store_id: str = Header(..., alias="X-Store-Id"),
):
    """创建配送订单"""
    delivery = await delivery_db.create_delivery(
        store_id=x_store_id,
        order_id=request.order_id,
        pickup_address=request.pickup_address,
        delivery_address=request.delivery_address,
        customer_name=request.customer_name,
        customer_phone=request.customer_phone,
        notes=request.notes,
    )
    return {
        "success": True,
        "data": delivery,
        "message": f"配送订单创建成功，配送单号：{delivery['id']}，骑手 {delivery['driver_name']} 将在约 {delivery['estimated_time']} 分钟内送达",
    }


@router.get("/deliveries")
async def get_deliveries(
    status: Optional[str] = None,
    limit: int = 50,
    x_store_id: str = Header(..., alias="X-Store-Id"),
):
    """获取门店配送列表"""
    deliveries = await delivery_db.get_deliveries(store_id=x_store_id, status=status, limit=limit)
    return {"success": True, "data": deliveries, "message": "获取配送列表成功"}


@router.get("/deliveries/{delivery_id}")
async def get_delivery(
    delivery_id: int,
    x_store_id: str = Header(..., alias="X-Store-Id"),
):
    """获取配送详情"""
    delivery = await delivery_db.get_delivery(delivery_id, store_id=x_store_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="配送订单不存在")
    delivery["status_text"] = DELIVERY_STATUS.get(delivery["status"], delivery["status"])
    return {"success": True, "data": delivery, "message": "获取配送详情成功"}


@router.get("/deliveries/order/{order_id}")
async def get_delivery_by_order(
    order_id: int,
    x_store_id: str = Header(..., alias="X-Store-Id"),
):
    """根据订单 ID 获取配送信息"""
    delivery = await delivery_db.get_delivery_by_order(order_id, store_id=x_store_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="该订单暂无配送信息")
    delivery["status_text"] = DELIVERY_STATUS.get(delivery["status"], delivery["status"])
    return {"success": True, "data": delivery, "message": "获取配送信息成功"}


@router.put("/deliveries/{delivery_id}/status")
async def update_delivery_status(
    delivery_id: int,
    request: UpdateDeliveryStatusRequest,
    x_store_id: str = Header(..., alias="X-Store-Id"),
):
    """更新配送状态"""
    if request.status not in DELIVERY_STATUS:
        raise HTTPException(
            status_code=400,
            detail=f"无效的状态，可选值：{list(DELIVERY_STATUS.keys())}",
        )
    delivery = await delivery_db.update_delivery_status(delivery_id, request.status, store_id=x_store_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="配送订单不存在")
    delivery["status_text"] = DELIVERY_STATUS.get(delivery["status"], delivery["status"])
    return {
        "success": True,
        "data": delivery,
        "message": f"配送状态已更新为：{DELIVERY_STATUS[request.status]}",
    }


@router.get("/status-options")
async def get_status_options():
    """获取配送状态选项"""
    return {"success": True, "data": DELIVERY_STATUS, "message": "获取状态选项成功"}

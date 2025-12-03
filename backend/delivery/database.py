"""
送了么配送数据库
"""
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Optional
import random
import sys

sys.path.append(str(Path(__file__).parent.parent))
from shared.database import DATA_DIR

# 数据库路径
DELIVERY_DB_PATH = DATA_DIR / "delivery.db"


class DeliveryDatabase:
    """送了么配送数据库管理"""

    # 模拟骑手列表
    DRIVERS = [
        {"name": "张师傅", "phone": "138****1234"},
        {"name": "李师傅", "phone": "139****5678"},
        {"name": "王师傅", "phone": "137****9012"},
        {"name": "赵师傅", "phone": "136****3456"},
        {"name": "刘师傅", "phone": "135****7890"},
    ]

    def __init__(self, db_path: Path = DELIVERY_DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        """初始化数据库，创建表"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    order_source TEXT DEFAULT 'xixi_coffee',
                    pickup_address TEXT NOT NULL,
                    delivery_address TEXT NOT NULL,
                    customer_name TEXT,
                    customer_phone TEXT,
                    status TEXT DEFAULT 'pending',
                    driver_name TEXT,
                    driver_phone TEXT,
                    estimated_time INTEGER,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    picked_at TEXT,
                    delivered_at TEXT
                )
            """)
            await db.commit()

    async def create_delivery(
        self,
        order_id: int,
        pickup_address: str,
        delivery_address: str,
        customer_name: str,
        customer_phone: str,
        notes: Optional[str] = None,
    ) -> dict:
        """创建配送订单"""
        now = datetime.now().isoformat()

        # 随机分配骑手
        driver = random.choice(self.DRIVERS)
        # 预估配送时间 20-45 分钟
        estimated_time = random.randint(20, 45)

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO deliveries 
                (order_id, pickup_address, delivery_address, customer_name, customer_phone, 
                 status, driver_name, driver_phone, estimated_time, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    pickup_address,
                    delivery_address,
                    customer_name,
                    customer_phone,
                    "assigned",
                    driver["name"],
                    driver["phone"],
                    estimated_time,
                    notes,
                    now,
                    now,
                ),
            )
            await db.commit()
            delivery_id = cursor.lastrowid

            return {
                "id": delivery_id,
                "order_id": order_id,
                "pickup_address": pickup_address,
                "delivery_address": delivery_address,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "status": "assigned",
                "driver_name": driver["name"],
                "driver_phone": driver["phone"],
                "estimated_time": estimated_time,
                "notes": notes,
                "created_at": now,
                "updated_at": now,
            }

    async def get_delivery(self, delivery_id: int) -> Optional[dict]:
        """获取配送详情"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM deliveries WHERE id = ?", (delivery_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_delivery_by_order(self, order_id: int) -> Optional[dict]:
        """根据订单 ID 获取配送信息"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM deliveries WHERE order_id = ? ORDER BY created_at DESC LIMIT 1",
                (order_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_deliveries(
        self, status: Optional[str] = None, limit: int = 50
    ) -> list[dict]:
        """获取配送列表"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if status:
                cursor = await db.execute(
                    "SELECT * FROM deliveries WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status, limit),
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM deliveries ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                )

            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def update_delivery_status(
        self, delivery_id: int, status: str
    ) -> Optional[dict]:
        """更新配送状态"""
        now = datetime.now().isoformat()

        async with aiosqlite.connect(self.db_path) as db:
            if status == "picked":
                await db.execute(
                    "UPDATE deliveries SET status = ?, picked_at = ?, updated_at = ? WHERE id = ?",
                    (status, now, now, delivery_id),
                )
            elif status == "delivered":
                await db.execute(
                    "UPDATE deliveries SET status = ?, delivered_at = ?, updated_at = ? WHERE id = ?",
                    (status, now, now, delivery_id),
                )
            else:
                await db.execute(
                    "UPDATE deliveries SET status = ?, updated_at = ? WHERE id = ?",
                    (status, now, delivery_id),
                )

            await db.commit()
            return await self.get_delivery(delivery_id)


# 配送状态说明
DELIVERY_STATUS = {
    "pending": "待分配",
    "assigned": "已分配骑手",
    "picked": "已取货",
    "delivering": "配送中",
    "delivered": "已送达",
    "cancelled": "已取消",
}

# 全局数据库实例
delivery_db = DeliveryDatabase()


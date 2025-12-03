"""
希希咖啡店数据库
"""
import aiosqlite
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import sys

sys.path.append(str(Path(__file__).parent.parent))
from shared.database import DATA_DIR

# 数据库路径
COFFEE_DB_PATH = DATA_DIR / "coffee.db"


class CoffeeDatabase:
    """希希咖啡店数据库管理"""

    def __init__(self, db_path: Path = COFFEE_DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        """初始化数据库，创建表和初始数据"""
        async with aiosqlite.connect(self.db_path) as db:
            # 创建商品表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    image_url TEXT,
                    available INTEGER DEFAULT 1
                )
            """)

            # 创建订单表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    items TEXT NOT NULL,
                    total REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    customer_name TEXT,
                    customer_phone TEXT,
                    customer_address TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            await db.commit()

            # 检查是否需要插入初始数据
            cursor = await db.execute("SELECT COUNT(*) FROM products")
            count = await cursor.fetchone()

            if count[0] == 0:
                await self._insert_initial_products(db)

    async def _insert_initial_products(self, db: aiosqlite.Connection):
        """插入初始商品数据"""
        products = [
            # 经典咖啡
            ("美式咖啡", 18.0, "经典美式，浓郁醇厚", "经典咖啡", "☕", 1),
            ("拿铁咖啡", 22.0, "意式浓缩加丝滑牛奶", "经典咖啡", "🥛", 1),
            ("卡布奇诺", 24.0, "浓缩咖啡、蒸奶和奶泡的完美结合", "经典咖啡", "☕", 1),
            ("摩卡咖啡", 26.0, "咖啡与巧克力的甜蜜邂逅", "经典咖啡", "🍫", 1),
            ("焦糖玛奇朵", 26.0, "焦糖与咖啡的层次享受", "经典咖啡", "🍯", 1),
            # 特调饮品
            ("冰摇柠檬茶", 16.0, "清爽柠檬配红茶", "特调饮品", "🍋", 1),
            ("芒果冰沙", 20.0, "新鲜芒果打制", "特调饮品", "🥭", 1),
            ("抹茶拿铁", 24.0, "日式抹茶与牛奶的融合", "特调饮品", "🍵", 1),
            ("草莓星冰乐", 28.0, "草莓与冰沙的夏日清凉", "特调饮品", "🍓", 1),
            # 甜点
            ("提拉米苏", 32.0, "经典意式甜点", "甜点", "🍰", 1),
            ("芝士蛋糕", 28.0, "浓郁芝士香", "甜点", "🧀", 1),
            ("巧克力布朗尼", 22.0, "浓郁巧克力口感", "甜点", "🍫", 1),
            ("可颂面包", 15.0, "法式酥脆可颂", "甜点", "🥐", 1),
        ]

        await db.executemany(
            "INSERT INTO products (name, price, description, category, image_url, available) VALUES (?, ?, ?, ?, ?, ?)",
            products,
        )
        await db.commit()

    async def get_products(self, category: Optional[str] = None) -> list[dict]:
        """获取商品列表"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if category:
                cursor = await db.execute(
                    "SELECT * FROM products WHERE category = ? AND available = 1",
                    (category,),
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM products WHERE available = 1"
                )

            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_product_by_id(self, product_id: int) -> Optional[dict]:
        """根据 ID 获取商品"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM products WHERE id = ?", (product_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_product_by_name(self, name: str) -> Optional[dict]:
        """根据名称获取商品"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM products WHERE name LIKE ?", (f"%{name}%",)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def create_order(
        self,
        items: list[dict],
        customer_name: str,
        customer_phone: str,
        customer_address: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """创建订单"""
        total = sum(item["price"] * item["quantity"] for item in items)
        now = datetime.now().isoformat()

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO orders (items, total, status, customer_name, customer_phone, customer_address, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    json.dumps(items, ensure_ascii=False),
                    total,
                    "pending",
                    customer_name,
                    customer_phone,
                    customer_address,
                    notes,
                    now,
                    now,
                ),
            )
            await db.commit()
            order_id = cursor.lastrowid

            return {
                "id": order_id,
                "items": items,
                "total": total,
                "status": "pending",
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "customer_address": customer_address,
                "notes": notes,
                "created_at": now,
                "updated_at": now,
            }

    async def get_order(self, order_id: int) -> Optional[dict]:
        """获取订单详情"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            row = await cursor.fetchone()

            if row:
                order = dict(row)
                order["items"] = json.loads(order["items"])
                return order
            return None

    async def get_orders(
        self, status: Optional[str] = None, limit: int = 50
    ) -> list[dict]:
        """获取订单列表"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if status:
                cursor = await db.execute(
                    "SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status, limit),
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,)
                )

            rows = await cursor.fetchall()
            orders = []
            for row in rows:
                order = dict(row)
                order["items"] = json.loads(order["items"])
                orders.append(order)
            return orders

    async def update_order_status(
        self, order_id: int, status: str
    ) -> Optional[dict]:
        """更新订单状态"""
        now = datetime.now().isoformat()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, order_id),
            )
            await db.commit()

            return await self.get_order(order_id)


# 全局数据库实例
coffee_db = CoffeeDatabase()


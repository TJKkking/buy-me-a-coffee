"""
希希咖啡店数据库 - 多门店版
"""
import aiosqlite
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import sys

sys.path.append(str(Path(__file__).parent.parent))
from shared.database import DATA_DIR

COFFEE_DB_PATH = DATA_DIR / "coffee.db"


class CoffeeDatabase:
    """希希咖啡店数据库管理（多门店）"""

    def __init__(self, db_path: Path = COFFEE_DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        """初始化数据库，创建表和初始数据"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL DEFAULT '希希咖啡店',
                    address TEXT NOT NULL,
                    phone TEXT,
                    business_hours TEXT DEFAULT '8:00-22:00',
                    status TEXT DEFAULT 'open',
                    created_at TEXT NOT NULL
                )
            """)

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

            await db.execute("""
                CREATE TABLE IF NOT EXISTS store_product_availability (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_id TEXT NOT NULL,
                    product_id INTEGER NOT NULL,
                    available INTEGER DEFAULT 1,
                    stock INTEGER DEFAULT -1,
                    updated_at TEXT,
                    UNIQUE(store_id, product_id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_id TEXT NOT NULL DEFAULT 'default',
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

            cursor = await db.execute("SELECT COUNT(*) FROM products")
            count = await cursor.fetchone()
            if count[0] == 0:
                await self._insert_initial_products(db)

            cursor = await db.execute("SELECT COUNT(*) FROM stores")
            count = await cursor.fetchone()
            if count[0] == 0:
                await self._insert_initial_stores(db)

    async def _insert_initial_products(self, db: aiosqlite.Connection):
        """插入初始商品数据（共享菜单）"""
        products = [
            ("美式咖啡", 18.0, "经典美式，浓郁醇厚", "经典咖啡", "☕", 1),
            ("拿铁咖啡", 22.0, "意式浓缩加丝滑牛奶", "经典咖啡", "🥛", 1),
            ("卡布奇诺", 24.0, "浓缩咖啡、蒸奶和奶泡的完美结合", "经典咖啡", "☕", 1),
            ("摩卡咖啡", 26.0, "咖啡与巧克力的甜蜜邂逅", "经典咖啡", "🍫", 1),
            ("焦糖玛奇朵", 26.0, "焦糖与咖啡的层次享受", "经典咖啡", "🍯", 1),
            ("冰摇柠檬茶", 16.0, "清爽柠檬配红茶", "特调饮品", "🍋", 1),
            ("芒果冰沙", 20.0, "新鲜芒果打制", "特调饮品", "🥭", 1),
            ("抹茶拿铁", 24.0, "日式抹茶与牛奶的融合", "特调饮品", "🍵", 1),
            ("草莓星冰乐", 28.0, "草莓与冰沙的夏日清凉", "特调饮品", "🍓", 1),
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

    async def _insert_initial_stores(self, db: aiosqlite.Connection):
        """插入初始门店和商品可用状态"""
        now = datetime.now().isoformat()
        stores = [
            ("store_001", "希希咖啡店", "人民路88号", "021-12345678", "8:00-22:00", "open", now),
            ("store_002", "希希咖啡店", "中关村大街1号", "010-87654321", "7:30-21:30", "open", now),
            ("store_003", "希希咖啡店", "南京东路100号", "021-11111111", "8:00-23:00", "open", now),
        ]
        await db.executemany(
            "INSERT INTO stores (store_id, name, address, phone, business_hours, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            stores,
        )

        cursor = await db.execute("SELECT id FROM products")
        product_ids = [row[0] for row in await cursor.fetchall()]

        availability = []
        for store_id, *_ in stores:
            for pid in product_ids:
                availability.append((store_id, pid, 1, -1, now))

        await db.executemany(
            "INSERT INTO store_product_availability (store_id, product_id, available, stock, updated_at) VALUES (?, ?, ?, ?, ?)",
            availability,
        )
        await db.commit()

    # ==================== 门店管理 ====================

    async def get_stores(self) -> list[dict]:
        """获取所有门店列表"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM stores ORDER BY id")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_store(self, store_id: str) -> Optional[dict]:
        """根据 store_id 获取门店详情"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM stores WHERE store_id = ?", (store_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    # ==================== 商品查询 ====================

    async def get_products(self, store_id: str, category: Optional[str] = None) -> list[dict]:
        """获取门店可用商品列表"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            base_sql = """
                SELECT p.*, COALESCE(spa.available, 1) as store_available,
                       COALESCE(spa.stock, -1) as store_stock
                FROM products p
                LEFT JOIN store_product_availability spa
                    ON p.id = spa.product_id AND spa.store_id = ?
                WHERE p.available = 1 AND COALESCE(spa.available, 1) = 1
            """
            params: list = [store_id]
            if category:
                base_sql += " AND p.category = ?"
                params.append(category)

            cursor = await db.execute(base_sql, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_product_by_id(self, product_id: int) -> Optional[dict]:
        """根据 ID 获取商品（全局，不区分门店）"""
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

    # ==================== 订单管理 ====================

    async def create_order(
        self,
        store_id: str,
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
                INSERT INTO orders (store_id, items, total, status, customer_name, customer_phone, customer_address, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    store_id,
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
                "store_id": store_id,
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

    async def get_order(self, order_id: int, store_id: Optional[str] = None) -> Optional[dict]:
        """获取订单详情"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if store_id:
                cursor = await db.execute(
                    "SELECT * FROM orders WHERE id = ? AND store_id = ?",
                    (order_id, store_id),
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM orders WHERE id = ?", (order_id,)
                )
            row = await cursor.fetchone()
            if row:
                order = dict(row)
                order["items"] = json.loads(order["items"])
                return order
            return None

    async def get_orders(
        self, store_id: str, status: Optional[str] = None, limit: int = 50
    ) -> list[dict]:
        """获取门店订单列表"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if status:
                cursor = await db.execute(
                    "SELECT * FROM orders WHERE store_id = ? AND status = ? ORDER BY created_at DESC LIMIT ?",
                    (store_id, status, limit),
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM orders WHERE store_id = ? ORDER BY created_at DESC LIMIT ?",
                    (store_id, limit),
                )
            rows = await cursor.fetchall()
            orders = []
            for row in rows:
                order = dict(row)
                order["items"] = json.loads(order["items"])
                orders.append(order)
            return orders

    async def update_order_status(
        self, order_id: int, status: str, store_id: Optional[str] = None
    ) -> Optional[dict]:
        """更新订单状态"""
        now = datetime.now().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            if store_id:
                await db.execute(
                    "UPDATE orders SET status = ?, updated_at = ? WHERE id = ? AND store_id = ?",
                    (status, now, order_id, store_id),
                )
            else:
                await db.execute(
                    "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
                    (status, now, order_id),
                )
            await db.commit()
            return await self.get_order(order_id, store_id)

    # ==================== 商品可用状态管理（管理端 Agent 预留）====================

    async def update_product_availability(
        self, store_id: str, product_id: int, available: int, stock: Optional[int] = None,
    ) -> Optional[dict]:
        """设置门店商品可用状态（沽清/恢复）"""
        now = datetime.now().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            if stock is not None:
                await db.execute(
                    """
                    INSERT INTO store_product_availability (store_id, product_id, available, stock, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(store_id, product_id) DO UPDATE SET available=?, stock=?, updated_at=?
                    """,
                    (store_id, product_id, available, stock, now, available, stock, now),
                )
            else:
                await db.execute(
                    """
                    INSERT INTO store_product_availability (store_id, product_id, available, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(store_id, product_id) DO UPDATE SET available=?, updated_at=?
                    """,
                    (store_id, product_id, available, now, available, now),
                )
            await db.commit()

            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT p.*, spa.available as store_available, spa.stock as store_stock
                FROM products p
                JOIN store_product_availability spa ON p.id = spa.product_id
                WHERE spa.store_id = ? AND spa.product_id = ?
                """,
                (store_id, product_id),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    # ==================== 门店经营统计（管理端 Agent 预留）====================

    async def get_store_stats(self, store_id: str) -> dict:
        """获取门店经营统计"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) as total, COALESCE(SUM(total), 0) as revenue FROM orders WHERE store_id = ? AND created_at >= ?",
                (store_id, today),
            )
            row = await cursor.fetchone()
            today_orders, today_revenue = row[0], row[1]

            cursor = await db.execute(
                "SELECT status, COUNT(*) as cnt FROM orders WHERE store_id = ? AND created_at >= ? GROUP BY status",
                (store_id, today),
            )
            status_dist = {r[0]: r[1] for r in await cursor.fetchall()}

            cursor = await db.execute(
                "SELECT COUNT(*) FROM orders WHERE store_id = ?", (store_id,)
            )
            total_orders = (await cursor.fetchone())[0]

            return {
                "store_id": store_id,
                "today_orders": today_orders,
                "today_revenue": float(today_revenue),
                "today_status_distribution": status_dist,
                "total_orders": total_orders,
            }


coffee_db = CoffeeDatabase()

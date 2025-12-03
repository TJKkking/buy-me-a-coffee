from shared.server import build_fastapi_app
from config import API_HOST, DELIVERY_API_PORT
from .api import router


async def lifespan(app):
    from .database import delivery_db

    await delivery_db.init_db()


app = build_fastapi_app(
    DELIVERY_API_PORT,
    name="送了么配送后端服务",
    description="送了么配送的 REST API 服务，提供订单管理",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/delivery")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "delivery.main:app",
        host=API_HOST,
        port=DELIVERY_API_PORT,
        reload=False,
    )

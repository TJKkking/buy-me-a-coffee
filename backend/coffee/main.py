from shared.server import build_fastapi_app
from config import API_HOST, COFFEE_API_PORT
from .api import router


async def lifespan(app):
    from .database import coffee_db

    await coffee_db.init_db()


app = build_fastapi_app(
    COFFEE_API_PORT,
    name="希希咖啡店后端服务",
    description="希希咖啡店的 REST API 服务，提供商品和订单管理",
    lifespan=lifespan,
)

# 注册路由
app.include_router(router, prefix="/api/coffee")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "coffee.main:app",
        host=API_HOST,
        port=COFFEE_API_PORT,
        reload=False,
    )

from shared.server import build_fastapi_app
from config import API_HOST, DELIVERY_A2A_PORT, DELIVERY_A2A_URL
from .agent import delivery_agent
from shared.a2a import build_a2a_app


async def lifespan(app):
    a2a_app = await build_a2a_app(delivery_agent, DELIVERY_A2A_URL.replace("_", "-"))

    # 注册 A2A 路由
    a2a_app.add_routes_to_app(
        app,
        agent_card_url="/.well-known/agent-card.json",
        rpc_url="/",
    )

    print(
        f"🎫 Agent Card: http://0.0.0.0:{DELIVERY_A2A_PORT}/.well-known/agent-card.json"
    )


app = build_fastapi_app(
    DELIVERY_A2A_PORT, name="送了么配送服务 Agent", lifespan=lifespan
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "delivery.a2a:app",
        host=API_HOST,
        port=DELIVERY_A2A_PORT,
        reload=False,
    )

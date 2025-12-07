from config import API_HOST, COFFEE_A2A_PORT, COFFEE_A2A_URL
from .agent import coffee_agent
from shared.a2a import build_a2a_app
from shared.server import build_fastapi_app


async def lifespan(app):
    a2a_app = await build_a2a_app(coffee_agent, COFFEE_A2A_URL)

    # 注册 A2A 路由
    a2a_app.add_routes_to_app(
        app,
        agent_card_url="/.well-known/agent-card.json",
        rpc_url="/",
    )

    print(
        f"🎫 Agent Card: http://0.0.0.0:{COFFEE_A2A_PORT}/.well-known/agent-card.json"
    )


app = build_fastapi_app(COFFEE_A2A_PORT, name="送了么配送服务 Agent", lifespan=lifespan)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "coffee.a2a:app",
        host=API_HOST,
        port=COFFEE_A2A_PORT,
        reload=False,
    )

from typing import AsyncGenerator, Awaitable, Callable, Optional, Union
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI


def build_fastapi_app(
    port: int,
    *,
    name: str = "",
    description: str = "",
    lifespan: Optional[Callable[[FastAPI], Awaitable[None]]] = None,
):

    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        """应用生命周期"""
        print(f"🚀 正在启动 {name} ...")

        if lifespan is not None:
            await lifespan(app)

        print(f"✅ {name} 已启动")
        print(f"📍 地址: http://0.0.0.0:{port}")
        
        yield
        
        print(f"👋 {name} 已关闭")

    app = FastAPI(
        title=name,
        description=description,
        version="1.0.0",
        lifespan=_lifespan,
    )

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        """健康检查"""
        return {"name": name, "description": description}

    @app.get("/health")
    async def health():
        """健康检查"""
        return {"status": "healthy", "service": name}

    return app

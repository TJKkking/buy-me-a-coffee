"""
希希咖啡店服务模块

提供：
- 咖啡店后端 API (main.py)
- 咖啡店 Agent A2A (a2a.py)
- 咖啡店 Agent 定义 (agent.py)
- 咖啡店工具 (tools.py)
- 咖啡店数据库 (database.py)
- 咖啡店 API 路由 (api.py)
"""
from .agent import coffee_agent
from .api import router as api_router

__all__ = ["coffee_agent", "api_router"]

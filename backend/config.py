"""
配置文件

Buy A Coffee 多 Agent 系统配置

支持以下独立服务：
1. 咖啡店后端 API (COFFEE_API_PORT) - 提供咖啡店 REST API
2. 配送后端 API (DELIVERY_API_PORT) - 提供配送 REST API
3. 咖啡店 Agent A2A (COFFEE_A2A_PORT) - 咖啡店 A2A 服务
4. 配送 Agent A2A (DELIVERY_A2A_PORT) - 配送 A2A 服务
5. 主 Agent/网关 (GATEWAY_PORT) - 主入口，整合所有服务
"""

import os
from pathlib import Path
from dotenv import load_dotenv


# 加载环境变量
load_dotenv()


def get_env_with_default(default_value: str, *env_names: str) -> str:
    """按优先级获取环境变量值"""
    for name in env_names:
        value = os.getenv(name)
        if value is not None:
            return value
    return default_value


# AgentRun 集成能力
from agentrun.integration.google_adk import model, toolset

DEFAULT_LLM = model(
    get_env_with_default("sdk-test-model-service", "AGENTRUN_MODEL_NAME")
)

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 数据库目录
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# 数据库文件路径
COFFEE_DB_PATH = DATA_DIR / "coffee.db"
DELIVERY_DB_PATH = DATA_DIR / "delivery.db"


# 通用配置
API_HOST = get_env_with_default(
    "0.0.0.0",
    "API_HOST",
)

# 各服务端口配置
GATEWAY_PORT = int(
    get_env_with_default("8000", "GATEWAY_PORT", "FC_SERVER_PORT")
)  # 主网关/Agent
COFFEE_API_PORT = int(
    get_env_with_default("8001", "COFFEE_API_PORT", "FC_SERVER_PORT")
)  # 咖啡店后端 API
DELIVERY_API_PORT = int(
    get_env_with_default("8002", "DELIVERY_API_PORT", "FC_SERVER_PORT")
)  # 配送后端 API
COFFEE_A2A_PORT = int(
    get_env_with_default("8003", "COFFEE_A2A_PORT", "FC_SERVER_PORT")
)  # 咖啡店 Agent A2A
DELIVERY_A2A_PORT = int(
    get_env_with_default("8004", "DELIVERY_A2A_PORT", "FC_SERVER_PORT")
)  # 配送 Agent A2A


A2A_URLS = get_env_with_default("", "A2A_URLS").split(",") or []

# 服务 URL 配置（用于服务间调用）
COFFEE_API_URL = os.getenv("COFFEE_API_URL", f"http://localhost:{COFFEE_API_PORT}")
DELIVERY_API_URL = os.getenv(
    "DELIVERY_API_URL", f"http://localhost:{DELIVERY_API_PORT}"
)

COFFEE_A2A_URL = os.getenv("COFFEE_A2A_URL", f"http://localhost:{COFFEE_A2A_PORT}")
DELIVERY_A2A_URL = os.getenv("DELIVERY_A2A_URL", f"http://localhost:{COFFEE_A2A_PORT}")

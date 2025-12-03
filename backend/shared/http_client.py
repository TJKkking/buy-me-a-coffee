"""
HTTP 客户端工具 - 用于 Agent 工具通过 HTTP 接口调用后端服务

支持两种模式：
1. 统一部署：调用本地服务 (http://localhost:8000)
2. 分布式部署：调用外部服务 (通过环境变量配置)
"""

import requests
from typing import Optional
import logging
from concurrent.futures import ThreadPoolExecutor
from config import COFFEE_API_URL, DELIVERY_API_URL

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 独立的线程池，用于执行 HTTP 请求
_http_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="http_worker_")


def _make_request(method: str, url: str, **kwargs) -> dict:
    """在独立线程中执行 HTTP 请求"""
    try:
        logger.info(f"🌐 [HTTP Worker] {method} {url}")
        response = requests.request(method, url, timeout=30.0, **kwargs)
        response.raise_for_status()
        result = response.json()
        logger.info(f"🌐 [HTTP Worker] {method} {url} -> {response.status_code}")
        return {"success": True, "data": result}
    except requests.Timeout:
        logger.error(f"🌐 [HTTP Worker] {method} {url} 超时")
        return {"success": False, "error": f"HTTP {method} {url} 超时"}
    except requests.RequestException as e:
        logger.error(f"🌐 [HTTP Worker] {method} {url} 失败: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"🌐 [HTTP Worker] {method} {url} 异常: {e}")
        return {"success": False, "error": str(e)}


class APIClient:
    """API 客户端，用于调用后端 HTTP 接口"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        logger.info(f"🌐 [HTTP Client] 初始化, base_url={base_url}")

    def _build_url(self, path: str) -> str:
        """构建完整 URL"""
        return f"{self.base_url}{path}"

    def _execute(self, method: str, path: str, **kwargs) -> dict:
        """执行 HTTP 请求（通过线程池）"""
        url = self._build_url(path)
        logger.info(f"🌐 [HTTP] 提交请求: {method} {path}")

        future = _http_executor.submit(_make_request, method, url, **kwargs)
        result = future.result(timeout=35.0)

        if not result["success"]:
            raise Exception(result["error"])

        return result["data"]

    def get(self, path: str, params: Optional[dict] = None) -> dict:
        """发送 GET 请求"""
        return self._execute("GET", path, params=params)

    def post(self, path: str, json: Optional[dict] = None) -> dict:
        """发送 POST 请求"""
        return self._execute("POST", path, json=json)

    def put(self, path: str, json: Optional[dict] = None) -> dict:
        """发送 PUT 请求"""
        return self._execute("PUT", path, json=json)

    def delete(self, path: str) -> dict:
        """发送 DELETE 请求"""
        return self._execute("DELETE", path)


# ==================== 咖啡店 API 客户端 ====================

_coffee_api_client: Optional[APIClient] = None


def get_coffee_api_client() -> APIClient:
    """获取咖啡店 API 客户端"""
    global _coffee_api_client
    if _coffee_api_client is None:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).parent.parent))

        _coffee_api_client = APIClient(base_url=COFFEE_API_URL)
    return _coffee_api_client


# ==================== 配送 API 客户端 ====================

_delivery_api_client: Optional[APIClient] = None


def get_delivery_api_client() -> APIClient:
    """获取配送 API 客户端"""
    global _delivery_api_client
    if _delivery_api_client is None:
        _delivery_api_client = APIClient(base_url=DELIVERY_API_URL)
    return _delivery_api_client


# ==================== 兼容旧接口 ====================


def get_api_client() -> APIClient:
    """获取通用 API 客户端（兼容旧代码）"""
    return get_coffee_api_client()

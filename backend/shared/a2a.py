from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.auth.credential_service.in_memory_credential_service import (
    InMemoryCredentialService,
)
from google.adk.agents.base_agent import BaseAgent
import httpx
import logging

logger = logging.getLogger("google_adk." + __name__)

STORE_STATE_KEYS = ("store_id", "store_name", "store_address", "store_display_name")


class StoreAwareA2aExecutor(A2aAgentExecutor):
    """扩展 A2aAgentExecutor，从 A2A 请求 metadata 中提取门店信息写入远程 session state。

    Gateway 通过 RemoteA2aAgent 的 a2a_request_meta_provider 将门店信息
    注入 SendMessageRequest.metadata，本 Executor 在创建 session 后将其
    桥接到 session.state，使远程 Agent 的工具函数能通过 ToolContext.state
    读取 store_id，与统一部署模式行为一致。
    """

    async def _prepare_session(self, context, run_request, runner):
        session = await super()._prepare_session(context, run_request, runner)
        metadata = getattr(context, "metadata", None)
        if metadata:
            injected = []
            for key in STORE_STATE_KEYS:
                if key in metadata and key not in session.state:
                    session.state[key] = metadata[key]
                    injected.append(key)
            if injected:
                logger.info(
                    "Injected store metadata into remote session: %s",
                    ", ".join(f"{k}={session.state[k]}" for k in injected),
                )
        return session


async def build_a2a_app(agent: BaseAgent, base_url: str) -> A2AStarletteApplication:
    """构建 A2A 应用"""

    async def create_runner() -> Runner:
        return Runner(
            app_name=agent.name,
            agent=agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
            credential_service=InMemoryCredentialService(),
        )

    task_store = InMemoryTaskStore()
    agent_executor = StoreAwareA2aExecutor(runner=create_runner)
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=task_store,
    )

    # 构建 Agent Card
    rpc_url = f"{base_url}/"
    card_builder = AgentCardBuilder(
        agent=agent,
        rpc_url=rpc_url,
    )
    agent_card = await card_builder.build()

    # 创建 A2A 应用
    a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    return a2a_app


async def get_agent_card_json(url: str):

    async with httpx.AsyncClient() as client:
        # 确保 URL 以 /.well-known/agent.json 结尾
        agent_card_url = url
        if not agent_card_url.endswith("/.well-known/agent-card.json"):
            if agent_card_url.endswith("/"):
                agent_card_url = f"{agent_card_url}.well-known/agent-card.json"
            else:
                agent_card_url = f"{agent_card_url}/.well-known/agent-card.json"

        response = await client.get(agent_card_url, timeout=5.0)

        return agent_card_url, response.json()

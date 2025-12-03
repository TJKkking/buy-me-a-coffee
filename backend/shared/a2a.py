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
    agent_executor = A2aAgentExecutor(runner=create_runner)
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

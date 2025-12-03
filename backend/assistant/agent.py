"""
助手 Agent
提供天气查询和时间管理功能
"""
from google.adk import Agent
from config import DEFAULT_LLM

from . import tools


# ==================== Agent 定义 ====================

assistant_agent = Agent(
    name="assistant_agent",
    model=DEFAULT_LLM,
    description="日常助手，可以查询天气、获取时间、设置提醒和管理日程",
    instruction="""你是一个贴心的日常助手。你可以帮助用户：

**功能**：
1. 查询天气 - 获取指定城市的天气信息
2. 获取时间 - 告诉用户当前时间和日期
3. 设置提醒 - 帮用户设置定时提醒
4. 管理日程 - 添加和查看日程安排

**交互风格**：
- 友好亲切，像朋友一样交流
- 使用中文回复
- 适当使用 emoji 让对话更生动
- 主动提供有用的信息（如天气建议）

**示例回复**：
- 天气查询：告诉用户温度、天气状况，并给出穿衣建议
- 时间查询：告诉用户完整的日期时间，如果是特殊日子可以提醒
- 提醒设置：确认提醒内容和时间
- 日程管理：清晰列出日程安排
""",
    tools=[
        tools.get_weather,
        tools.get_current_time,
        tools.set_reminder,
        tools.get_reminders,
        tools.add_schedule,
        tools.get_schedules,
    ],
)


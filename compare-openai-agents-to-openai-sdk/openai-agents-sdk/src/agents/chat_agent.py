from datetime import date

from agents import Agent, RunContextWrapper
from src.agents.context import ChatContext
from src.hooks.chat_agent_hooks import ChatAgentHooks
from src.llm_config import get_default_model
from src.services.storage import get_session_title


async def _instructions(ctx: RunContextWrapper[ChatContext], agent: Agent) -> str:
    session_title = await get_session_title(ctx.context.session_id)
    today = date.today().strftime("%B %d, %Y")

    base = f"You are a helpful assistant. Today's date is {today}."

    if session_title:
        return f"{base}\nThis conversation title is: {session_title}."
    return base


chat_agent = Agent(
    name="ChatAgent",
    instructions=_instructions,
    model=get_default_model(),
    hooks=ChatAgentHooks(),
)

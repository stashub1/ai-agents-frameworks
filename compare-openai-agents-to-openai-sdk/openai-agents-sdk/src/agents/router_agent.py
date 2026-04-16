from typing import Literal

from agents import Agent
from pydantic import BaseModel

from src.llm_config import get_default_model


class RouterDecision(BaseModel):
    agent: Literal["chat_agent", "task_manager"]


router_agent = Agent(
    name="Router",
    model=get_default_model(),
    output_type=RouterDecision,
    instructions="""
Classify the user message to route it to the correct agent.

- "task_manager": the user is requesting an action to be done, asking to create or track a task,
  or assigning work to be completed
- "chat_agent": everything else — general questions, conversation, information requests
""",
)

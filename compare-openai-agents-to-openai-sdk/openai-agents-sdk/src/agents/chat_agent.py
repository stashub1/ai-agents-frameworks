from agents import Agent
from src.llm_config import get_default_model

chat_agent = Agent(
    name="ChatAgent",
    instructions="You are a helpful assistant.",
    model=get_default_model(),
)

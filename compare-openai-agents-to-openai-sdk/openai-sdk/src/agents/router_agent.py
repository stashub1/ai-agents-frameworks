import json
from typing import Literal

from src.llm_config import MODEL, get_client
from src.tracing import log_request, log_response

_SYSTEM = """
Classify the user message to route it to the correct agent.
Respond with JSON only: {"agent": "chat_agent"} or {"agent": "task_manager"}.

- "task_manager": the user is requesting an action to be done, asking to create or track a task,
  or assigning work to be completed
- "chat_agent": everything else — general questions, conversation, information requests
"""


async def route(messages: list[dict]) -> Literal["chat_agent", "task_manager"]:
    client = get_client()
    request_messages = [{"role": "system", "content": _SYSTEM}] + messages

    log_request("Router", MODEL, request_messages)

    response = await client.chat.completions.create(
        model=MODEL,
        messages=request_messages,
        response_format={"type": "json_object"},
    )

    log_response("Router", response)

    try:
        data = json.loads(response.choices[0].message.content)
        agent = data.get("agent", "chat_agent")
        if agent not in ("chat_agent", "task_manager"):
            return "chat_agent"
        return agent
    except (json.JSONDecodeError, AttributeError):
        return "chat_agent"

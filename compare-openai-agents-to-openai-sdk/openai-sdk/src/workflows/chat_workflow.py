from collections.abc import AsyncGenerator

from src.agents import chat_agent, task_manager_agent
from src.agents.context import ChatContext
from src.agents.router_agent import route
from src.services.storage import get_history, save_new_messages


async def stream_response(
    session_id: str,
    user_id: str,
    message: str,
) -> AsyncGenerator[str | dict, None]:
    context = ChatContext(user_id=user_id, session_id=session_id)

    # ---------------------------------------- Load history ----------------------------------------

    # Load history — strip agent metadata, it's not part of the OpenAI message schema
    history = [{"role": m["role"], "content": m["content"]} for m in await get_history(session_id)]

    # ---------------------------------------- Route ----------------------------------------

    yield {"routing": True}
    router_input = history[-5:] + [{"role": "user", "content": message}]
    agent_name = await route(router_input)

    # ---------------------------------------- Notify frontend ----------------------------------------

    display_name = chat_agent.NAME if agent_name == "chat_agent" else task_manager_agent.NAME
    yield {"agent": display_name}

    # ---------------------------------------- Stream chosen agent ----------------------------------------

    trimmed_history = history[-10:]
    full_input = trimmed_history + [{"role": "user", "content": message}]

    if agent_name == "chat_agent":
        generator = chat_agent.run(full_input)
    else:
        generator = task_manager_agent.run(full_input, context)

    chunks: list[str] = []
    async for chunk in generator:
        chunks.append(chunk)
        yield chunk

    # ---------------------------------------- Persist ----------------------------------------

    full_response = "".join(chunks)
    new_messages = [
        {"role": "user", "content": message},
        {"role": "assistant", "content": full_response},
    ]
    title = message[:60] if message else None
    await save_new_messages(session_id, user_id, new_messages, title=title, agent=display_name)

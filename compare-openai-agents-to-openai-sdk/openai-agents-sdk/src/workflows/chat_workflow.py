import inspect
from collections.abc import AsyncGenerator

from agents import Agent, Runner, RunContextWrapper
from openai.types.responses import ResponseTextDeltaEvent

from src.agents.chat_agent import chat_agent
from src.agents.context import ChatContext
from src.agents.router_agent import router_agent
from src.agents.task_manager_agent import task_manager_agent
from src.services.notifications import send_user_data
from src.services.storage import get_history, save_new_messages

AGENT_MAP = {
    "chat_agent": chat_agent,
    "task_manager": task_manager_agent,
}


async def stream_response(
    session_id: str,
    user_id: str,
    message: str,
) -> AsyncGenerator[str | dict, None]:
    context = ChatContext(user_id=user_id, session_id=session_id)
    history = await _load_history(session_id)

    # Route based on last 5 messages
    yield {"routing": True}
    router_input = history[-5:] + [{"role": "user", "content": message}]

    router_instructions = await _resolve_instructions(router_agent)
    yield {"agent_call": _build_call_info(router_agent, router_instructions, router_input, role="router")}

    decision = await Runner.run(router_agent, input=router_input)
    route = decision.final_output.agent

    if route == "send_user_data":
        yield {"decision_function": "send_user_data"}
        await send_user_data(user_id=user_id, email=f"{user_id}@example.com")
        yield "Your data has been sent to your email."
        return

    chosen_agent = AGENT_MAP[route]

    # Notify frontend which agent was chosen
    yield {"agent": chosen_agent.name}

    # Stream chosen agent with last 10 messages
    trimmed_history = history[-10:]
    full_input = trimmed_history + [{"role": "user", "content": message}]

    chosen_instructions = await _resolve_instructions(chosen_agent, context)
    yield {"agent_call": _build_call_info(chosen_agent, chosen_instructions, full_input, role="main")}

    text_yielded = False
    result = Runner.run_streamed(chosen_agent, input=full_input, context=context)
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            yield event.data.delta
            text_yielded = True

    # When StopAtTools fires, no LLM runs so no text deltas are emitted.
    # Deliver the tool return value directly.
    if not text_yielded and isinstance(result.final_output, str) and result.final_output:
        yield result.final_output

    await _persist_turn(session_id, user_id, message, result, trimmed_history, chosen_agent.name)


async def _load_history(session_id: str) -> list[dict]:
    rows = await get_history(session_id)
    return [{"role": m["role"], "content": m["content"]} for m in rows]


async def _persist_turn(
    session_id: str,
    user_id: str,
    message: str,
    result,
    trimmed_history: list[dict],
    agent_name: str,
) -> None:
    new_messages = [
        _normalize(m) for m in result.to_input_list()[len(trimmed_history):]
        if m.get("role") in ("user", "assistant")
    ]
    await save_new_messages(session_id, user_id, new_messages, title=message[:60], agent=agent_name)


async def _resolve_instructions(agent: Agent, context: ChatContext | None = None) -> str:
    if isinstance(agent.instructions, str):
        return agent.instructions
    if context is None:
        return "<dynamic>"
    wrapper = RunContextWrapper(context=context)
    result = agent.instructions(wrapper, agent)
    if inspect.isawaitable(result):
        return await result
    return str(result)


def _model_name(agent: Agent) -> str:
    if isinstance(agent.model, str):
        return agent.model
    return getattr(agent.model, "model", str(agent.model))


def _build_call_info(agent: Agent, instructions: str, messages: list[dict], role: str) -> dict:
    s = agent.model_settings
    return {
        "role": role,
        "name": agent.name,
        "instructions": instructions,
        "model": _model_name(agent),
        "temperature": s.temperature,
        "top_p": s.top_p,
        "max_tokens": s.max_tokens,
        "tools": [t.name for t in agent.tools],
        "output_type": str(agent.output_type) if agent.output_type else None,
        "message_count": len(messages),
    }


def _normalize(msg: dict) -> dict:
    """Convert Responses API content blocks to plain strings for Chat Completions compatibility."""
    content = msg.get("content", "")

    if not isinstance(content, list):
        return msg

    text = "".join(
        part.get("text", "")
        for part in content
        if isinstance(part, dict) and part.get("type") == "output_text"
    )
    return {"role": msg["role"], "content": text}

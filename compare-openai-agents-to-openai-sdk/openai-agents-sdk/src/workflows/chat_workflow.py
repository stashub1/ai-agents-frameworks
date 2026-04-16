import json
from collections.abc import AsyncGenerator

from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent

from src.agents.chat_agent import chat_agent
from src.agents.context import ChatContext
from src.agents.router_agent import router_agent
from src.agents.task_manager_agent import task_manager_agent
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

    # Load history — strip agent metadata, it's not part of the OpenAI message schema
    history = [{"role": m["role"], "content": m["content"]} for m in await get_history(session_id)]

    # Route based on last 5 messages
    yield {"routing": True}
    router_input = history[-5:] + [{"role": "user", "content": message}]
    decision = await Runner.run(router_agent, input=router_input)
    chosen_agent = AGENT_MAP[decision.final_output.agent]

    # Notify frontend which agent was chosen
    yield {"agent": chosen_agent.name}

    # Stream chosen agent with last 10 messages
    trimmed_history = history[-10:]
    full_input = trimmed_history + [{"role": "user", "content": message}]

    _log_request(chosen_agent, full_input)

    result = Runner.run_streamed(chosen_agent, input=full_input, context=context)
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            yield event.data.delta

    # Persist new messages from this turn
    new_messages = [
        _normalize(m) for m in result.to_input_list()[len(trimmed_history):]
        if m.get("role") in ("user", "assistant")
    ]
    title = message[:60] if message else None
    await save_new_messages(session_id, user_id, new_messages, title=title, agent=chosen_agent.name)


def _log_request(agent: Agent, full_input: list[dict]) -> None:
    s = agent.model_settings
    print("\n── request to model ──")
    model = agent.model if isinstance(agent.model, str) else agent.model.model
    print(f"  model:              {model}")
    print(f"  system:             {agent.instructions}")
    print(f"  temperature:        {s.temperature}")
    print(f"  top_p:              {s.top_p}")
    print(f"  max_tokens:         {s.max_tokens}")
    print(f"  frequency_penalty:  {s.frequency_penalty}")
    print(f"  presence_penalty:   {s.presence_penalty}")
    print(f"  tool_choice:        {s.tool_choice}")
    print(f"  tools:              {[t.name for t in agent.tools] or '[]'}")
    print(f"  input_guardrails:   {agent.input_guardrails or '[]'}")
    print(f"  output_guardrails:  {agent.output_guardrails or '[]'}")
    print(f"  output_type:        {agent.output_type}")
    print("  messages:")
    print(json.dumps(full_input, indent=2, ensure_ascii=False))
    print("─────────────────────\n")


def _normalize(msg: dict) -> dict:
    """Convert Responses API content blocks to plain strings for Chat Completions compatibility."""
    content = msg.get("content", "")

    if not isinstance(content, list):
        return msg

    # Extract text from output_text blocks
    text = "".join(
        part.get("text", "")
        for part in content
        if isinstance(part, dict) and part.get("type") == "output_text"
    )
    return {"role": msg["role"], "content": text}

# src/agents/hooks.py
from __future__ import annotations

import logging
import time
from typing import Any

from agents.run_context import AgentHookContext, RunContextWrapper

from agents import Agent, AgentHooks
from src.agents.context import ChatContext
from src.services.storage import save_new_messages

logger = logging.getLogger(__name__)


class ChatAgentHooks(AgentHooks[ChatContext]):
    async def on_start(
        self,
        context: AgentHookContext[ChatContext],
        agent: Agent,
    ) -> None:
        logger.info(
            "Agent started",
            extra={
                "agent_name": agent.name,
                "user_id": context.context.user_id,
                "session_id": context.context.session_id,
            },
        )

    async def on_llm_start(
        self,
        context: RunContextWrapper[ChatContext],
        agent: Agent,
        system_prompt: str | None,
        input_items: list[Any],
    ) -> None:
        # Start a timer for this model call.
        # Since ChatContext is your own dataclass, you can safely attach runtime fields to it.
        context.context._llm_started_at = time.perf_counter()

        logger.info(
            "LLM call started",
            extra={
                "agent_name": agent.name,
                "user_id": context.context.user_id,
                "session_id": context.context.session_id,
                "input_items_count": len(input_items),
                "has_system_prompt": bool(system_prompt),
                "system_prompt_length": len(system_prompt) if system_prompt else 0,
            },
        )

    async def on_llm_end(
        self,
        context: RunContextWrapper[ChatContext],
        agent: Agent,
        response: Any,
    ) -> None:
        started_at = getattr(context.context, "_llm_started_at", None)
        duration_ms = None
        if started_at is not None:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

        logger.info(
            "LLM call finished",
            extra={
                "agent_name": agent.name,
                "user_id": context.context.user_id,
                "session_id": context.context.session_id,
                "duration_ms": duration_ms,
                "usage": str(context.usage),
                "output_items_count": len(response.output)
                if hasattr(response, "output")
                else None,
            },
        )

    async def on_end(
        self,
        context: AgentHookContext[ChatContext],
        agent: Agent,
        output: Any,
    ) -> None:
        # Persist final assistant output
        await save_new_messages(
            session_id=context.context.session_id,
            user_id=context.context.user_id,
            new_messages=[
                {
                    "role": "assistant",
                    "content": output,
                }
            ],
            agent=agent.name,
        )

        logger.info(
            "Agent finished",
            extra={
                "agent_name": agent.name,
                "user_id": context.context.user_id,
                "session_id": context.context.session_id,
                "usage": str(context.usage),
            },
        )

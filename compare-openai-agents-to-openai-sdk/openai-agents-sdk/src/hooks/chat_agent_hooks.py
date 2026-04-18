from __future__ import annotations

import json
import logging
import time
from typing import Any

from agents import Agent, AgentHooks
from agents.run_context import RunContextWrapper

from src.agents.context import ChatContext

logger = logging.getLogger(__name__)


def _format_output_text(response: Any, max_len: int = 500) -> str | None:
    output_text = None

    if hasattr(response, "output") and response.output:
        try:
            text_parts: list[str] = []
            for item in response.output:
                if not hasattr(item, "content") or not item.content:
                    continue
                for part in item.content:
                    if getattr(part, "type", None) == "output_text":
                        text = getattr(part, "text", None)
                        if text:
                            text_parts.append(text)
            output_text = "\n".join(text_parts) if text_parts else None
        except Exception:
            output_text = str(response.output)

    if output_text and len(output_text) > max_len:
        output_text = output_text[:max_len] + "...[truncated]"

    return output_text


class ChatAgentHooks(AgentHooks[ChatContext]):
    async def on_llm_start(
        self,
        context: RunContextWrapper[ChatContext],
        agent: Agent,
        system_prompt: str | None,
        input_items: list[Any],
    ) -> None:
        context.context._llm_started_at = time.perf_counter()

        pretty_prompt = system_prompt or ""

        logger.info(
            f"[LLM START]\n"
            f"Agent: {agent.name}\n"
            f"User ID: {context.context.user_id}\n"
            f"Session ID: {context.context.session_id}\n"
            f"Prompt:\n{pretty_prompt}\n"
            f"Input items count: {len(input_items)}\n"
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

        usage = context.usage
        pretty_usage = json.dumps(
            {
                "requests": getattr(usage, "requests", None),
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )
        output_text = _format_output_text(response)

        step_label = (
            "[LLM END - FINAL TEXT]"
            if output_text
            else "[LLM END - TOOL CALL OR EMPTY]"
        )

        logger.info(
            f"{step_label}\n"
            f"Agent: {agent.name}\n"
            f"User ID: {context.context.user_id}\n"
            f"Session ID: {context.context.session_id}\n"
            f"Duration: {duration_ms} ms\n"
            f"Usage:\n{pretty_usage}\n"
            f"Output:\n{output_text}"
        )

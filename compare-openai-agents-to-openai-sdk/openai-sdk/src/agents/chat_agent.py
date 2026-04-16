from collections.abc import AsyncGenerator

from src.llm_config import MODEL, get_client
from src.tracing import log_request

NAME = "ChatAgent"

_SYSTEM = "You are a helpful assistant."


async def run(messages: list[dict]) -> AsyncGenerator[str, None]:
    client = get_client()
    request_messages = [{"role": "system", "content": _SYSTEM}] + messages

    log_request(NAME, MODEL, request_messages, stream=True)

    stream = await client.chat.completions.create(
        model=MODEL,
        messages=request_messages,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

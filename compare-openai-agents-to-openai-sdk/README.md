# OpenAI SDK vs OpenAI Agents SDK — Chat App Comparison

This repo explores building the same chat application twice — once with the raw OpenAI Python SDK, and once with the OpenAI Agents SDK — to see how the two approaches differ in practice.

## What we built

A multi-session chat app with:

- **Session management** — each user gets persistent, named chat sessions stored in SQLite
- **Router agent** — classifies each incoming message and dispatches it to the right agent
- **Chat agent** — handles general conversation
- **Task manager agent** — lets users create, list, and delete tasks via tool calls

Both implementations share the same FastAPI server, SQLite storage layer, and static frontend. Only the agent logic differs.

## Projects

| Folder | Approach |
|---|---|
| `openai-sdk/` | Raw OpenAI Python SDK — everything built by hand |
| `openai-agents-sdk/` | OpenAI Agents SDK — framework handles the plumbing |

---

## Differences

### Agent definition

**openai-sdk** — an agent is a plain async function. You manually prepend the system prompt, call the API, and yield chunks:

```python
async def run(messages: list[dict]) -> AsyncGenerator[str, None]:
    request_messages = [{"role": "system", "content": _SYSTEM}] + messages
    stream = await client.chat.completions.create(model=MODEL, messages=request_messages, stream=True)
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
```

**openai-agents-sdk** — an agent is a declarative object. No API calls, no message construction:

```python
chat_agent = Agent(
    name="ChatAgent",
    instructions="You are a helpful assistant.",
    model=get_default_model(),
)
```

---

### Structured output (router)

**openai-sdk** — you tell the model to respond with JSON, then parse and validate it yourself:

```python
response = await client.chat.completions.create(
    model=MODEL,
    messages=request_messages,
    response_format={"type": "json_object"},
)
data = json.loads(response.choices[0].message.content)
agent = data.get("agent", "chat_agent")
if agent not in ("chat_agent", "task_manager"):
    return "chat_agent"
```

**openai-agents-sdk** — you define a Pydantic model and the framework enforces it:

```python
class RouterDecision(BaseModel):
    agent: Literal["chat_agent", "task_manager"]

router_agent = Agent(
    name="Router",
    output_type=RouterDecision,
    instructions="...",
)

decision = await Runner.run(router_agent, input=router_input)
chosen_agent = AGENT_MAP[decision.final_output.agent]
```

No JSON parsing. No fallback handling. The type is guaranteed.

---

### Tool calls (task manager)

**openai-sdk** — tools are defined as raw JSON schemas (~40 lines), then you write a manual dispatch loop: call the model, check for tool calls, execute them, append results, loop again, then stream a final response. The agentic loop is entirely your responsibility (~80 lines total).

**openai-agents-sdk** — tools are plain Python functions decorated with `@function_tool`. The framework generates the JSON schema from type hints, handles the tool call loop, and streams the final response automatically (~55 lines total, no loop code):

```python
@function_tool
async def create_task(ctx: RunContextWrapper[ChatContext], title: str, description: str) -> str:
    await save_task(ctx.context.user_id, title, description)
    return f"Task created: {title}"
```

Context (user ID, session ID) flows in automatically via `RunContextWrapper` — no need to thread it through manually.

---

### Streaming

**openai-sdk** — you own the stream loop and pull deltas from `chunk.choices[0].delta.content`.

**openai-agents-sdk** — you call `Runner.run_streamed()` and filter for `ResponseTextDeltaEvent`:

```python
result = Runner.run_streamed(chosen_agent, input=full_input, context=context)
async for event in result.stream_events():
    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
        yield event.data.delta
```

More verbose event filtering, but the framework handles all the intermediate tool call streaming internally.

---

## Why openai-agents-sdk is less code

| Concern | openai-sdk | openai-agents-sdk |
|---|---|---|
| Tool schema | Hand-written JSON (~40 lines) | Auto-generated from type hints |
| Tool call loop | Manual while loop | Built into the runner |
| Structured output | JSON parse + validation | Pydantic model, guaranteed |
| Context passing | Explicit parameter on every call | Injected via `RunContextWrapper` |
| Agent definition | Async function + API call | Declarative `Agent(...)` object |

The raw SDK gives you full control and zero magic. It's the right choice when you need to understand exactly what's happening or when the framework abstractions don't fit your use case. The Agents SDK trades that visibility for significantly less boilerplate — the agentic loop, tool dispatch, schema generation, and structured output handling all disappear into the framework.

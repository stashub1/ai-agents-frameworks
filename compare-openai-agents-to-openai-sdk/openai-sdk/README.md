# Chat App — OpenAI SDK

A multi-session chat application built with the raw [OpenAI Python SDK](https://github.com/openai/openai-python) — no agent framework. All routing, tool call loops, structured output parsing, and streaming are implemented by hand.

## What it does

- **Multi-session chat** — each user gets persistent, named chat sessions stored in SQLite
- **Router agent** — classifies each message with a JSON-mode call and dispatches to the right agent
- **Chat agent** — handles general conversation
- **Task manager agent** — lets users create, list, and delete tasks; manages the tool call loop manually
- **Streaming** — responses stream token by token to the frontend via SSE
- **Admin UI** — view all sessions and tasks at `/admin` and `/tasks`

## Stack

- [OpenAI Python SDK](https://github.com/openai/openai-python) — direct API calls, no framework
- [FastAPI](https://fastapi.tiangolo.com/) — HTTP server and SSE streaming
- [aiosqlite](https://aiosqlite.omnilib.dev/) — async SQLite for sessions and tasks
- Model: `gpt-4o-mini`

Works with OpenAI or any OpenAI-compatible API (e.g. Nebius).

## Getting started

**1. Install dependencies**

```bash
uv sync
```

**2. Configure your API key**

```bash
cp .env.example .env
# then edit .env — for OpenAI:
# OPENAI_API_KEY=sk-...
#
# or for a compatible provider like Nebius:
# NEBIUS_API_KEY=...
# NEBIUS_BASE_URL=https://api.studio.nebius.ai/v1
```

**3. Start the server**

```bash
uv run server.py
```

The app runs at `http://localhost:8001`.

## Project structure

```
server.py                   # FastAPI routes and SSE endpoint
src/
  agents/
    chat_agent.py           # Async generator — calls API and streams chunks
    router_agent.py         # JSON-mode call, parses and validates response manually
    task_manager_agent.py   # Manual tool call loop + streaming final response
    context.py              # ChatContext (user_id, session_id)
  services/
    storage.py              # All session and message queries
  workflows/
    chat_workflow.py        # Routing, streaming, and persistence logic
  database.py               # SQLite schema init
  llm_config.py             # Model name and AsyncOpenAI client factory
  tracing.py                # Request/response console logging
static/                     # Frontend (HTML/CSS/JS)
```

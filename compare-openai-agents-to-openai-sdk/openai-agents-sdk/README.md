# Chat App — OpenAI Agents SDK

A multi-session chat application built with the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python). Demonstrates how to build a router + multi-agent system using the framework's declarative approach.

## What it does

- **Multi-session chat** — each user gets persistent, named chat sessions stored in SQLite
- **Router agent** — classifies each message and dispatches to the right agent using structured output (`output_type`)
- **Chat agent** — handles general conversation
- **Task manager agent** — lets users create, list, and delete tasks via `@function_tool` decorated functions
- **Streaming** — responses stream token by token to the frontend via SSE
- **Admin UI** — view all sessions and tasks at `/admin` and `/tasks`

## Stack

- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) — agent framework
- [FastAPI](https://fastapi.tiangolo.com/) — HTTP server and SSE streaming
- [aiosqlite](https://aiosqlite.omnilib.dev/) — async SQLite for sessions and tasks
- Model: `gpt-4o-mini`

## Getting started

**1. Install dependencies**

```bash
uv sync
```

**2. Set your OpenAI API key**

```bash
cp .env.example .env
# then edit .env and add your key:
# OPENAI_API_KEY=sk-...
```

**3. Start the server**

```bash
uv run server.py
```

The app runs at `http://localhost:8000`.

## Project structure

```
server.py                   # FastAPI routes and SSE endpoint
src/
  agents/
    chat_agent.py           # General conversation agent
    router_agent.py         # Classifies messages, returns structured output
    task_manager_agent.py   # Task CRUD via @function_tool
    context.py              # ChatContext (user_id, session_id)
  services/
    storage.py              # All session and message queries
  workflows/
    chat_workflow.py        # Routing, streaming, and persistence logic
  database.py               # SQLite schema init
  llm_config.py             # Model name
static/                     # Frontend (HTML/CSS/JS)
```

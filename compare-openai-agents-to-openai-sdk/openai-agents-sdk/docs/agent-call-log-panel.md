# Agent Call Log Panel

A right-side panel that shows a live log of every agent call made during a conversation.

## What it shows

Each message send triggers two agent calls — one to the **Router** and one to the **chosen agent** (ChatAgent or TaskManager). Each call appears as a collapsible card showing:

- Badge: `router` or `main`
- Agent name
- Model, temperature, max tokens, message count chips
- System prompt (resolved — dynamic instructions like `ChatAgent` are resolved with the current session context)
- Tools list
- Output type (if structured)

## How it works

**Backend** (`src/workflows/chat_workflow.py`):
- Before running the router, `_extract_instructions` reads its string instructions and `_build_call_info` assembles the metadata dict.
- Before streaming the chosen agent, `_resolve_instructions` calls the async instructions function (if callable) via `RunContextWrapper`, falling back to `"<dynamic>"` on error.
- Both are yielded as `{"agent_call": {...}}` SSE events.

**Frontend** (`static/app.js`):
- The SSE loop handles `parsed.agent_call` by calling `appendLogEntry(call)`.
- Entries are collapsible (click header to expand/collapse).
- The × button in the panel header clears all entries.

**Styles** (`static/style.css`): `.logs-panel`, `.log-entry`, `.log-entry-body`, etc.

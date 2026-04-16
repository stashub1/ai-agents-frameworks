import json
from collections.abc import AsyncGenerator

from src.agents.context import ChatContext
from src.llm_config import MODEL, get_client
from src.services.storage import delete_task_by_id, get_tasks_by_user, save_task
from src.tracing import log_request, log_response

NAME = "TaskManagerAgent"

_SYSTEM = """
You help users create, view, and delete tasks.

To create a task:
- Call create_task with a title (max 10 words) and full description.

To delete a task:
- Call list_user_tasks to find the task ID.
- Call delete_task with the correct task_id.

To list tasks:
- Call list_user_tasks and present the results clearly.

Always confirm the outcome to the user.
"""

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create and log a task requested by the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short summary of the task (max 10 words)"},
                    "description": {"type": "string", "description": "Full description of what needs to be done"},
                },
                "required": ["title", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_user_tasks",
            "description": "List all tasks belonging to the current user.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "The ID of the task to delete"},
                },
                "required": ["task_id"],
            },
        },
    },
]


async def _execute_tool(name: str, args: dict, context: ChatContext) -> str:
    if name == "create_task":
        await save_task(context.user_id, args["title"], args["description"])
        return f"Task created: {args['title']}"

    if name == "list_user_tasks":
        tasks = await get_tasks_by_user(context.user_id)
        if not tasks:
            return "No tasks found."
        lines = [f"ID {t['id']}: {t['title']} [{t['status']}]" for t in tasks]
        return "\n".join(lines)

    if name == "delete_task":
        deleted = await delete_task_by_id(args["task_id"], context.user_id)
        if deleted:
            return f"Task {args['task_id']} deleted successfully."
        return f"Task {args['task_id']} not found."

    return "Unknown tool"


async def run(messages: list[dict], context: ChatContext) -> AsyncGenerator[str, None]:
    client = get_client()
    working_messages = [{"role": "system", "content": _SYSTEM}] + messages

    # ---------------------------------------- Tool call loop ----------------------------------------

    while True:
        log_request(NAME, MODEL, working_messages, tools=_TOOLS)

        response = await client.chat.completions.create(
            model=MODEL,
            messages=working_messages,
            tools=_TOOLS,
            tool_choice="auto",
        )

        log_response(NAME, response)

        msg = response.choices[0].message

        if not msg.tool_calls:
            break

        working_messages.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ],
        })

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = await _execute_tool(tc.function.name, args, context)
            working_messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    # ---------------------------------------- Streaming final response ----------------------------------------

    log_request(NAME, MODEL, working_messages, stream=True)

    stream = await client.chat.completions.create(
        model=MODEL,
        messages=working_messages,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

from agents import Agent, RunContextWrapper, function_tool

from src.agents.context import ChatContext
from src.llm_config import get_default_model
from src.services.storage import delete_task_by_id, get_tasks_by_user, save_task


@function_tool
async def create_task(
    ctx: RunContextWrapper[ChatContext],
    title: str,
    description: str,
) -> str:
    await save_task(ctx.context.user_id, title, description)
    return f"Task created: {title}"


@function_tool
async def list_user_tasks(ctx: RunContextWrapper[ChatContext]) -> str:
    tasks = await get_tasks_by_user(ctx.context.user_id)
    if not tasks:
        return "No tasks found."
    lines = [f"ID {t['id']}: {t['title']} [{t['status']}]" for t in tasks]
    return "\n".join(lines)


@function_tool
async def delete_task(ctx: RunContextWrapper[ChatContext], task_id: int) -> str:
    deleted = await delete_task_by_id(task_id, ctx.context.user_id)
    if deleted:
        return f"Task {task_id} deleted successfully."
    return f"Task {task_id} not found."


task_manager_agent = Agent[ChatContext](
    name="TaskManagerAgent",
    model=get_default_model(),
    tools=[create_task, list_user_tasks, delete_task],
    instructions="""
You help users create, view, and delete tasks.

To create a task:
- Call create_task with a title (max 10 words) and full description.

To delete a task:
- Call list_user_tasks to find the task ID.
- Call delete_task with the correct task_id.

To list tasks:
- Call list_user_tasks and present the results clearly.

Always confirm the outcome to the user.
""",
)

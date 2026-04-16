import json
import time

import aiosqlite

from src.database import DB_PATH


# ---------------------------------------- Sessions ----------------------------------------

async def list_sessions(user_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, title, created_at, updated_at FROM sessions WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def list_all_sessions() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT s.id, s.user_id, s.title, s.created_at, s.updated_at,
                   COUNT(m.id) AS message_count
            FROM sessions s
            LEFT JOIN messages m ON m.session_id = s.id
            GROUP BY s.id
            ORDER BY s.updated_at DESC
        """) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def delete_session(session_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        await db.commit()


# ---------------------------------------- Messages ----------------------------------------

async def get_history(session_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT role, content, agent FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [{"role": row[0], "content": json.loads(row[1]), "agent": row[2]} for row in rows]


async def save_new_messages(
    session_id: str,
    user_id: str,
    new_messages: list[dict],
    title: str | None = None,
    agent: str | None = None,
) -> None:
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        await _upsert_session(db, session_id, user_id, title, now)
        await _insert_messages(db, session_id, new_messages, now, agent=agent)
        await db.commit()


# ---------------------------------------- Tasks ----------------------------------------

async def list_tasks() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, user_id, title, description, status, created_at FROM tasks ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def save_task(user_id: str, title: str, description: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO tasks (user_id, title, description, created_at) VALUES (?, ?, ?, ?)",
            (user_id, title, description, time.time()),
        )
        await db.commit()


async def get_tasks_by_user(user_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, title, description, status FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def delete_task_by_id(task_id: int, user_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
        ) as cursor:
            if not await cursor.fetchone():
                return False
        await db.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        await db.commit()
        return True


# ---------------------------------------- Helpers ----------------------------------------

async def _upsert_session(
    db: aiosqlite.Connection,
    session_id: str,
    user_id: str,
    title: str | None,
    now: float,
) -> None:
    async with db.execute(
        "SELECT title FROM sessions WHERE id = ?", (session_id,)
    ) as cursor:
        existing = await cursor.fetchone()

    if existing is None:
        await db.execute(
            "INSERT INTO sessions (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, user_id, title or "New conversation", now, now),
        )
        return

    should_set_title = title and existing[0] == "New conversation"
    if should_set_title:
        await db.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
            (title, now, session_id),
        )
    else:
        await db.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (now, session_id),
        )


async def _insert_messages(
    db: aiosqlite.Connection,
    session_id: str,
    messages: list[dict],
    now: float,
    agent: str | None = None,
) -> None:
    for msg in messages:
        content = msg.get("content", "")
        msg_agent = agent if msg["role"] == "assistant" else None
        await db.execute(
            "INSERT INTO messages (session_id, role, content, agent, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, msg["role"], json.dumps(content), msg_agent, now),
        )

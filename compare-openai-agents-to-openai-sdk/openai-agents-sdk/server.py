# load_dotenv must run before any agents imports — _debug flags are set at import time
from dotenv import load_dotenv
load_dotenv()

import json

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.database import init_db
from src.services.storage import delete_session, get_history, list_all_sessions, list_sessions, list_tasks
from src.tracing import setup_tracing
from src.workflows import stream_response

setup_tracing()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup():
    await init_db()


class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    message: str


# ── Pages ─────────────────────────────────────────────────
@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/admin")
async def admin():
    return FileResponse("static/admin.html")


@app.get("/tasks")
async def tasks():
    return FileResponse("static/maintenance.html")


# ── API ───────────────────────────────────────────────────
@app.get("/api/sessions")
async def get_sessions(user_id: str):
    return await list_sessions(user_id)


@app.get("/api/admin/sessions")
async def get_all_sessions():
    return await list_all_sessions()


@app.get("/api/tasks")
async def get_tasks():
    return await list_tasks()


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    history = await get_history(session_id)
    if not history:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "history": history}


@app.delete("/api/sessions/{session_id}")
async def remove_session(session_id: str):
    await delete_session(session_id)
    return {"ok": True}


@app.post("/api/chat/stream")
async def chat_stream(body: ChatRequest):
    async def generate():
        async for item in stream_response(body.session_id, body.user_id, body.message):
            if isinstance(item, dict):
                yield f"data: {json.dumps(item)}\n\n"
            else:
                yield f"data: {json.dumps({'content': item})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

import uuid
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from app.agent import Agent
from app.memory import MemoryStore

app = FastAPI(title="Recall Chat Agent", version="1.0.0")
memory = MemoryStore()
agent = Agent(memory=memory)


class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None, max_length=100)
    message: str = Field(min_length=1, max_length=12000)


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    created_at: str
    sources: list[dict]
    search_used: bool


@app.get("/health")
async def health():
    return {"status": "ok", "service": "recall"}


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    session_id = payload.session_id or str(uuid.uuid4())
    try:
        return await agent.respond(session_id, payload.message.strip())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/sessions")
async def sessions(limit: int = Query(default=20, ge=1, le=100)):
    return {"sessions": memory.list_sessions(limit)}


@app.get("/sessions/{session_id}/messages")
async def session_messages(session_id: str, limit: int = Query(default=50, ge=1, le=100)):
    return {"messages": memory.list_messages(session_id, limit)}

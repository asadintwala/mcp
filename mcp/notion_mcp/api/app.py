"""FastAPI application — the main API gateway.

Endpoints
---------
POST /chat              Send a message, get AI response (with tool calls via MCP)
POST /sessions          Create a new chat session
GET  /sessions          List all sessions
GET  /sessions/{id}     Get session details + history
DELETE /sessions/{id}   Delete a session
GET  /health            Health check

Run with:
    uv run notion-api          (uses the script entry point)
    uv run uvicorn notion_mcp.api.app:app --reload   (dev mode)
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from notion_mcp.api.mcp_bridge import get_bridge
from notion_mcp.api.orchestrator import Orchestrator
from notion_mcp.api.session_store import store

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Globals populated at startup
# ---------------------------------------------------------------------------
_orchestrator: Orchestrator | None = None


# ---------------------------------------------------------------------------
# Lifespan — connect MCP bridge on startup, disconnect on shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hook."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        logger.error("GEMINI_API_KEY is not set")
        sys.exit(1)
    if not os.environ.get("NOTION_TOKEN"):
        logger.error("NOTION_TOKEN is not set")
        sys.exit(1)

    global _orchestrator

    # 1. Connect the MCP bridge (starts MCP server subprocess)
    bridge = await get_bridge()
    logger.info("MCP Bridge ready — %d tools available", len(bridge.tools))

    # 2. Initialise the Gemini orchestrator
    _orchestrator = Orchestrator(gemini_api_key=gemini_key)
    logger.info("Gemini Orchestrator initialised")

    yield  # App is running

    # Shutdown
    from notion_mcp.api.mcp_bridge import _bridge
    if _bridge:
        await _bridge.disconnect()
    logger.info("MCP Bridge disconnected — shutting down")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Notion MCP Orchestrator",
    description=(
        "AI-powered Notion assistant. Gemini Flash reasons about user intent, "
        "calls tools through the MCP server, and returns natural language answers."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str = Field(..., description="User's natural language message")
    session_id: str | None = Field(
        None,
        description="Session ID for context continuity. If omitted a new session is created.",
    )


class ChatResponse(BaseModel):
    session_id: str
    response: str
    created_session: bool = False


class SessionInfo(BaseModel):
    session_id: str
    created_at: str
    message_count: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message and get an AI-powered response.

    If ``session_id`` is provided, the conversation continues with existing
    history.  Otherwise a new session is created automatically.
    """
    created = False
    if req.session_id:
        session = store.get(req.session_id)
        if not session:
            raise HTTPException(404, f"Session '{req.session_id}' not found")
    else:
        session = store.create()
        created = True

    if _orchestrator is None:
        raise HTTPException(503, "Orchestrator not ready")

    answer = await _orchestrator.chat(req.message, session)

    return ChatResponse(
        session_id=session.session_id,
        response=answer,
        created_session=created,
    )


@app.post("/sessions", response_model=SessionInfo)
async def create_session():
    """Create a new empty chat session."""
    session = store.create()
    return SessionInfo(
        session_id=session.session_id,
        created_at=session.created_at,
        message_count=0,
    )


@app.get("/sessions", response_model=list[SessionInfo])
async def list_sessions():
    """List all active sessions."""
    return store.list_all()


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get full session details including history."""
    session = store.get(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")
    return {
        "session_id": session.session_id,
        "created_at": session.created_at,
        "message_count": len(session.history),
        "history": session.history,
    }


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its history."""
    if not store.delete(session_id):
        raise HTTPException(404, f"Session '{session_id}' not found")
    return {"deleted": True}


@app.get("/health")
async def health():
    """Health check."""
    from notion_mcp.api.mcp_bridge import _bridge
    return {
        "status": "ok",
        "mcp_connected": _bridge is not None and _bridge._session is not None,
        "tools_count": len(_bridge.tools) if _bridge else 0,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Start the FastAPI server via uvicorn."""
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    logger.info("Starting Notion MCP API on port %d", port)
    uvicorn.run(
        "notion_mcp.api.app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()

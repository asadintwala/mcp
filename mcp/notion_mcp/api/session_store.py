"""In-memory session store for chat history.

Each session holds the Gemini chat history so that context is preserved
across HTTP requests.  Sessions are keyed by a UUID generated on creation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Session:
    """A single user chat session."""

    session_id: str
    created_at: str
    history: list[dict[str, Any]] = field(default_factory=list)
    """Gemini-compatible message history (role + parts)."""


class SessionStore:
    """Thread-safe (GIL-protected) in-memory store of chat sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self) -> Session:
        sid = uuid.uuid4().hex
        session = Session(
            session_id=sid,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._sessions[sid] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def list_all(self) -> list[dict[str, Any]]:
        return [
            {
                "session_id": s.session_id,
                "created_at": s.created_at,
                "message_count": len(s.history),
            }
            for s in self._sessions.values()
        ]

    def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None


# Singleton instance shared across the FastAPI app
store = SessionStore()

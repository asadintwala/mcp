mcp-notion/
├── .env
├── .gitignore
├── CLAUDE.md
├── pyproject.toml
├── uv.lock
├── venv/
└── notion_mcp/
    ├── __init__.py
    ├── mcp_server.py          # FastMCP server
    ├── models.py              # Pydantic helpers
    ├── chat.py                # Direct Gemini CLI (bypasses MCP)
    ├── notion/
    │   └── mcp_client.py      # Notion SDK wrapper
    ├── tools/
    │   ├── search.py
    │   ├── pages.py
    │   ├── blocks.py
    │   ├── databases.py
    │   ├── comments.py
    │   └── users.py
    └── api/
        ├── app.py             # FastAPI entry
        ├── orchestrator.py    # Gemini + MCP bridge logic
        ├── mcp_bridge.py      # MCP client via HTTP
        ├── session_store.py   # In-memory sessions
        └── __init__.py
# Notion MCP Server (Python)
MCP server exposing Notion API as AI-accessible tools.
## Stack
- Python 3.11+, uv, mcp SDK (FastMCP)
- notion-client (official Notion SDK)
- pydantic for validation
## Commands
uv run notion-mcp-server          # start server (stdio)
uv run notion-mcp-server --http   # start server (streamable-http)
uv run pytest                     # run tests
uv add <pkg>                      # add dependency
## Project Structure
src/notion_mcp/
  mcp_server.py       # FastMCP init, lifecycle
  __init__.py     # entry
  notion/
    mcp_client.py     # NotionClient wrapper
  tools/
    pages.py      # search, create, retrieve, update, archive, move
    blocks.py     # retrieve_block_children, append_block_children
    databases.py  # retrieve_database, query/create data sources
    comments.py   # list, create comments
    users.py      # list, retrieve users
  models.py       # pydantic schemas
## Conventions
- One tool per function, decorated with @mcp.tool()
- Use async for any I/O-bound tools
- NOTION_TOKEN env var for auth
- All API responses: typed with pydantic
- Tests: pytest, co-located in tests/
## Key Decisions
- stdio transport default (--http for streamable)
- Notion API version 2025-09-03 (Data Source Edition)
- FastMCP high-level API (not low-level Server)
"""Notion MCP Server — entry point.

Start with stdio (default):
    NOTION_TOKEN=ntn_xxx uv run notion-mcp-server

Start with streamable-http:
    NOTION_TOKEN=ntn_xxx uv run notion-mcp-server --http --port 3000
"""

from __future__ import annotations

import argparse
import os
import sys

from notion_mcp import mcp

# Importing each tool module causes its @mcp.tool() decorators to execute,
# which registers all tools with the FastMCP server instance.
from notion_mcp.tools import (  # noqa: F401
    blocks,
    comments,
    databases,
    pages,
    search,
    users,
)


def main() -> None:
    """Parse CLI flags, validate the Notion token, and start the MCP server."""
    parser = argparse.ArgumentParser(description="Notion MCP Server")
    parser.add_argument(
        "--http",
        action="store_true",
        help="Use streamable-http transport instead of stdio",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port for HTTP transport (default: 3000)",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Validate NOTION_TOKEN early so users get a clear error on startup.
    # ------------------------------------------------------------------
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        print(
            "ERROR: NOTION_TOKEN environment variable is required.\n"
            "  1. Create an integration at https://www.notion.so/profile/integrations\n"
            "  2. Copy the ntn_xxx token\n"
            "  3. Export it:  export NOTION_TOKEN=ntn_xxx",
            file=sys.stderr,
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    # Start the server
    # ------------------------------------------------------------------
    if args.http:
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

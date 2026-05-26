"""Block tools — read and append block children."""

from __future__ import annotations

from notion_client.errors import APIResponseError

from notion_mcp import mcp
from notion_mcp.notion.mcp_client import get_client


@mcp.tool()
async def retrieve_block_children(block_id: str, page_size: int = 100) -> dict:
    """List child blocks of a page or block.

    Args:
        block_id: UUID of the parent page or block.
        page_size: Maximum number of blocks to return (1-100).

    Returns:
        A paginated list of child block objects.
    """
    try:
        client = get_client()
        return await client.retrieve_block_children(block_id, page_size=page_size)
    except APIResponseError as exc:
        return {"error": str(exc), "status": exc.status}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
async def append_block_children(block_id: str, children: list[dict]) -> dict:
    """Append new blocks to a page or block.

    Args:
        block_id: UUID of the parent page or block to append to.
        children: List of block objects in Notion API format, e.g.::

            [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "Hello!"}}
                        ]
                    }
                }
            ]

    Returns:
        The newly appended block objects.
    """
    try:
        client = get_client()
        return await client.append_block_children(block_id, children=children)
    except APIResponseError as exc:
        return {"error": str(exc), "status": exc.status}
    except Exception as exc:
        return {"error": str(exc)}

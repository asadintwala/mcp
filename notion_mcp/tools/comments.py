"""Comment tools — list and create comments on Notion pages."""

from __future__ import annotations

from notion_client.errors import APIResponseError

from notion_mcp import mcp
from notion_mcp.notion.mcp_client import get_client
from notion_mcp.models import make_rich_text


@mcp.tool()
def list_comments(block_id: str) -> dict:
    """List all comments on a page or block.

    Args:
        block_id: UUID of the page or block to list comments for.

    Returns:
        Paginated list of comment objects.
    """
    try:
        client = get_client()
        return client.list_comments(block_id)
    except APIResponseError as exc:
        return {"error": str(exc), "status": exc.status}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def create_comment(parent_id: str, text: str) -> dict:
    """Add a comment to a Notion page.

    Args:
        parent_id: UUID of the page to comment on.
        text: Plain-text comment body.

    Returns:
        The created comment object.
    """
    try:
        client = get_client()
        return client.create_comment(
            parent={"page_id": parent_id},
            rich_text=make_rich_text(text),
        )
    except APIResponseError as exc:
        return {"error": str(exc), "status": exc.status}
    except Exception as exc:
        return {"error": str(exc)}

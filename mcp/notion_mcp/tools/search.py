"""Search tool — find pages and data sources in Notion."""

from __future__ import annotations

from notion_client.errors import APIResponseError

from notion_mcp import mcp
from notion_mcp.notion.mcp_client import get_client


@mcp.tool()
async def search(query: str = "", filter_value: str = "page") -> dict:
    """Search Notion for pages or data sources.

    Args:
        query: The text to search for.
        filter_value: Object type filter — ``"page"`` or ``"data_source"``.

    Returns:
        Matching Notion objects sorted by last-edited time (descending).
    """
    if query is None:
        query = ""
    try:
        client = get_client()
        filter_param = {"value": filter_value, "property": "object"} if filter_value else None
        sort_param = {"direction": "descending", "timestamp": "last_edited_time"}
        return await client.search(query=query, filter=filter_param, sort=sort_param)
    except APIResponseError as exc:
        return {"error": str(exc), "status": exc.status}
    except Exception as exc:
        return {"error": str(exc)}

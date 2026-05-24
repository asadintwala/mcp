"""User tools — list workspace members and retrieve user details."""

from __future__ import annotations

from notion_client.errors import APIResponseError

from notion_mcp import mcp
from notion_mcp.notion.mcp_client import get_client


@mcp.tool()
def list_users() -> dict:
    """List all users in the Notion workspace.

    Returns:
        Paginated list of user objects (people and bots).
    """
    try:
        client = get_client()
        return client.list_users()
    except APIResponseError as exc:
        return {"error": str(exc), "status": exc.status}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def retrieve_user(user_id: str) -> dict:
    """Retrieve details for a single user.

    Args:
        user_id: UUID of the user.

    Returns:
        User object with name, avatar, email (if available), and type.
    """
    try:
        client = get_client()
        return client.retrieve_user(user_id)
    except APIResponseError as exc:
        return {"error": str(exc), "status": exc.status}
    except Exception as exc:
        return {"error": str(exc)}

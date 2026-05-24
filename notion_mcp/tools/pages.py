"""Page tools — CRUD operations on Notion pages."""

from __future__ import annotations

from notion_client.errors import APIResponseError

from notion_mcp import mcp
from notion_mcp.notion.mcp_client import get_client


@mcp.tool()
def retrieve_page(page_id: str) -> dict:
    """Retrieve a Notion page by its ID.

    Args:
        page_id: The UUID of the page (with or without dashes).

    Returns:
        Full page object including properties and metadata.
    """
    try:
        client = get_client()
        return client.retrieve_page(page_id)
    except APIResponseError as exc:
        return {"error": str(exc), "status": exc.status}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def create_page(
    parent_id: str,
    title: str,
    properties: dict | None = None,
    children: list[dict] | None = None,
) -> dict:
    """Create a new page under a parent page or database.

    The tool automatically detects whether *parent_id* refers to a database
    or a page and sets the parent accordingly.

    Args:
        parent_id: UUID of the parent page or database.
        title: Plain-text title for the new page.
        properties: Extra properties in Notion API format, e.g.
            ``{"Status": {"select": {"name": "Done"}}}``.
        children: Optional list of block children to include in the page body.

    Returns:
        The newly created page object.
    """
    try:
        client = get_client()
        title_prop = {"title": [{"type": "text", "text": {"content": title}}]}

        # Attempt database parent first, fall back to page parent.
        try:
            page_props = {"title": title_prop}
            if properties:
                page_props.update(properties)
            return client.create_page(
                parent={"database_id": parent_id},
                properties=page_props,
                children=children,
            )
        except APIResponseError:
            page_props = {"title": title_prop}
            if properties:
                page_props.update(properties)
            return client.create_page(
                parent={"page_id": parent_id},
                properties=page_props,
                children=children,
            )
    except APIResponseError as exc:
        return {"error": str(exc), "status": exc.status}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def update_page_properties(page_id: str, properties: dict) -> dict:
    """Update one or more properties of an existing page.

    Args:
        page_id: UUID of the page to update.
        properties: Properties to set, in Notion API format.

    Returns:
        The updated page object.
    """
    try:
        client = get_client()
        return client.update_page_properties(page_id, properties)
    except APIResponseError as exc:
        return {"error": str(exc), "status": exc.status}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def archive_page(page_id: str) -> dict:
    """Archive (soft-delete) a Notion page.

    The page can be restored later by setting ``archived`` back to ``false``.

    Args:
        page_id: UUID of the page to archive.

    Returns:
        The updated page object with ``archived: true``.
    """
    try:
        client = get_client()
        return client.update_page_properties(page_id, properties={}, archived=True)
    except APIResponseError as exc:
        return {"error": str(exc), "status": exc.status}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def move_page(page_id: str, new_parent_id: str) -> dict:
    """Move a page to a new parent page or database.

    Note: Direct parent updates may not be supported by all Notion API
    versions. If the move fails, an informative error is returned.

    Args:
        page_id: UUID of the page to move.
        new_parent_id: UUID of the target parent page or database.

    Returns:
        The updated page object, or an error dict.
    """
    try:
        client = get_client()

        # Try page parent first, then database parent.
        for parent_key in ("page_id", "database_id"):
            try:
                return client.client.pages.update(
                    page_id, parent={parent_key: new_parent_id},
                )
            except APIResponseError:
                continue

        return {
            "error": (
                "Move operation failed. The Notion API may not support "
                "moving this page via the API. Use the Notion UI instead."
            ),
        }
    except APIResponseError as exc:
        return {"error": str(exc), "status": exc.status}
    except Exception as exc:
        return {"error": str(exc)}

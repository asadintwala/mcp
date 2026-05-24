"""Database / Data Source tools — query, retrieve, and create."""

from __future__ import annotations

from notion_client.errors import APIResponseError

from notion_mcp import mcp
from notion_mcp.notion.mcp_client import get_client
from notion_mcp.models import make_rich_text


@mcp.tool()
def retrieve_database(database_id: str) -> dict:
    """Retrieve database metadata and schema.

    Args:
        database_id: UUID of the database.

    Returns:
        Database object including title, properties schema, and metadata.
    """
    try:
        client = get_client()
        return client.retrieve_database(database_id)
    except APIResponseError as exc:
        return {"error": str(exc), "status": exc.status}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def retrieve_data_source(data_source_id: str) -> dict:
    """Retrieve a data source (database) schema and properties.

    Alias for ``retrieve_database`` using the Notion API 2025-09-03
    *data source* terminology.

    Args:
        data_source_id: UUID of the data source.

    Returns:
        Data source object with schema information.
    """
    try:
        client = get_client()
        return client.retrieve_database(data_source_id)
    except APIResponseError as exc:
        return {"error": str(exc), "status": exc.status}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def query_data_source(
    data_source_id: str,
    filter: dict | None = None,
    sorts: list[dict] | None = None,
    page_size: int = 100,
) -> dict:
    """Query a data source (database) with optional filters and sorts.

    Args:
        data_source_id: UUID of the data source to query.
        filter: Notion filter object, e.g.
            ``{"property": "Status", "select": {"equals": "Done"}}``.
        sorts: List of sort objects, e.g.
            ``[{"property": "Created", "direction": "descending"}]``.
        page_size: Max results to return (1-100).

    Returns:
        Paginated list of page objects matching the query.
    """
    try:
        client = get_client()
        return client.query_database(
            database_id=data_source_id,
            filter=filter,
            sorts=sorts,
            page_size=page_size,
        )
    except APIResponseError as exc:
        return {"error": str(exc), "status": exc.status}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def create_data_source(
    parent_id: str,
    title: str,
    properties: dict,
) -> dict:
    """Create a new data source (database) under a parent page.

    Args:
        parent_id: UUID of the parent page.
        title: Plain-text title for the data source.
        properties: Property schema in Notion API format, e.g.::

            {
                "Name": {"title": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "To Do", "color": "red"},
                            {"name": "Done", "color": "green"}
                        ]
                    }
                }
            }

    Returns:
        The newly created data source object.
    """
    try:
        client = get_client()
        return client.create_database(
            parent={"page_id": parent_id},
            title=make_rich_text(title),
            properties=properties,
        )
    except APIResponseError as exc:
        return {"error": str(exc), "status": exc.status}
    except Exception as exc:
        return {"error": str(exc)}

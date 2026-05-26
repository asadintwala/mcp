"""Notion API wrapper with rate-limit retries and error handling."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from notion_client import AsyncClient
from notion_client.errors import APIResponseError

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds


class NotionClient:
    """Thin wrapper around the official Notion Python SDK.

    All methods return raw ``dict`` responses — FastMCP handles JSON
    serialisation for the AI client.
    """

    def __init__(self, token: str) -> None:
        self.client = AsyncClient(auth=token)

    # ------------------------------------------------------------------
    # Internal retry helper
    # ------------------------------------------------------------------

    @staticmethod
    async def _retry_on_rate_limit(func, *args, **kwargs) -> Any:
        """Call *func* with automatic retry on HTTP 429 (rate-limit)."""
        for attempt in range(MAX_RETRIES):
            try:
                return await func(*args, **kwargs)
            except APIResponseError as exc:
                if exc.status == 429 and attempt < MAX_RETRIES - 1:
                    wait = RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning("Rate-limited by Notion API. Retrying in %.1fs …", wait)
                    await asyncio.sleep(wait)
                else:
                    raise

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        filter: dict | None = None,
        sort: dict | None = None,
        page_size: int = 100,
    ) -> dict:
        kwargs: dict[str, Any] = {"query": query, "page_size": page_size}
        if filter is not None:
            kwargs["filter"] = filter
        if sort is not None:
            kwargs["sort"] = sort
        return await self._retry_on_rate_limit(self.client.search, **kwargs)

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------

    async def retrieve_page(self, page_id: str) -> dict:
        return await self._retry_on_rate_limit(self.client.pages.retrieve, page_id)

    async def create_page(
        self,
        parent: dict,
        properties: dict,
        children: list | None = None,
        icon: dict | None = None,
        cover: dict | None = None,
    ) -> dict:
        kwargs: dict[str, Any] = {"parent": parent, "properties": properties}
        if children:
            kwargs["children"] = children
        if icon:
            kwargs["icon"] = icon
        if cover:
            kwargs["cover"] = cover
        return await self._retry_on_rate_limit(self.client.pages.create, **kwargs)

    async def update_page_properties(
        self,
        page_id: str,
        properties: dict,
        icon: dict | None = None,
        cover: dict | None = None,
        archived: bool | None = None,
    ) -> dict:
        kwargs: dict[str, Any] = {"properties": properties}
        if icon is not None:
            kwargs["icon"] = icon
        if cover is not None:
            kwargs["cover"] = cover
        if archived is not None:
            kwargs["archived"] = archived
        return await self._retry_on_rate_limit(self.client.pages.update, page_id, **kwargs)

    # ------------------------------------------------------------------
    # Blocks
    # ------------------------------------------------------------------

    async def retrieve_block_children(self, block_id: str, page_size: int = 100) -> dict:
        return await self._retry_on_rate_limit(
            self.client.blocks.children.list, block_id, page_size=page_size,
        )

    async def append_block_children(self, block_id: str, children: list) -> dict:
        return await self._retry_on_rate_limit(
            self.client.blocks.children.append, block_id, children=children,
        )

    # ------------------------------------------------------------------
    # Databases / Data Sources
    # ------------------------------------------------------------------

    async def retrieve_database(self, database_id: str) -> dict:
        return await self._retry_on_rate_limit(self.client.databases.retrieve, database_id)

    async def query_database(
        self,
        database_id: str,
        filter: dict | None = None,
        sorts: list | None = None,
        page_size: int = 100,
    ) -> dict:
        kwargs: dict[str, Any] = {"database_id": database_id, "page_size": page_size}
        if filter:
            kwargs["filter"] = filter
        if sorts:
            kwargs["sorts"] = sorts
        return await self._retry_on_rate_limit(self.client.databases.query, **kwargs)

    async def create_database(self, parent: dict, title: list, properties: dict) -> dict:
        return await self._retry_on_rate_limit(
            self.client.databases.create, parent=parent, title=title, properties=properties,
        )

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    async def list_comments(self, block_id: str, page_size: int = 100) -> dict:
        return await self._retry_on_rate_limit(
            self.client.comments.list, block_id=block_id, page_size=page_size,
        )

    async def create_comment(
        self, parent: dict, rich_text: list, discussion_id: str | None = None,
    ) -> dict:
        kwargs: dict[str, Any] = {"parent": parent, "rich_text": rich_text}
        if discussion_id:
            kwargs["discussion_id"] = discussion_id
        return await self._retry_on_rate_limit(self.client.comments.create, **kwargs)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    async def list_users(self, page_size: int = 100) -> dict:
        return await self._retry_on_rate_limit(self.client.users.list, page_size=page_size)

    async def retrieve_user(self, user_id: str) -> dict:
        return await self._retry_on_rate_limit(self.client.users.retrieve, user_id)


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_client: NotionClient | None = None


def get_client() -> NotionClient:
    """Return (and lazily create) the global NotionClient singleton."""
    global _client
    if _client is None:
        token = os.environ.get("NOTION_TOKEN")
        if not token:
            raise RuntimeError(
                "NOTION_TOKEN environment variable is not set. "
                "Please export your Notion integration token."
            )
        _client = NotionClient(token)
    return _client

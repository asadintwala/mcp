"""Pydantic models and helper utilities for Notion API structures."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any


# ---------------------------------------------------------------------------
# Rich Text helpers
# ---------------------------------------------------------------------------

class RichTextItem(BaseModel):
    """A single rich text element."""
    type: str = "text"
    text: dict = Field(..., description='{"content": "...", "link": null}')
    annotations: dict | None = None


# ---------------------------------------------------------------------------
# Block helpers
# ---------------------------------------------------------------------------

class BlockChild(BaseModel):
    """Represents a block to append."""
    object: str = "block"
    type: str
    content: dict = Field(default_factory=dict, description="Type-specific payload")


# ---------------------------------------------------------------------------
# Convenience factories (return raw dicts for the Notion API)
# ---------------------------------------------------------------------------

def make_rich_text(content: str) -> list[dict]:
    """Create a Notion rich_text array from a plain string."""
    return [{"type": "text", "text": {"content": content}}]


def make_paragraph_block(content: str) -> dict:
    """Create a paragraph block dict."""
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": make_rich_text(content)},
    }


def make_heading_block(content: str, level: int = 1) -> dict:
    """Create a heading block (level 1-3)."""
    heading_type = f"heading_{min(max(level, 1), 3)}"
    return {
        "object": "block",
        "type": heading_type,
        heading_type: {"rich_text": make_rich_text(content)},
    }


def make_todo_block(content: str, checked: bool = False) -> dict:
    """Create a to-do block."""
    return {
        "object": "block",
        "type": "to_do",
        "to_do": {
            "rich_text": make_rich_text(content),
            "checked": checked,
        },
    }


def make_bulleted_list_block(content: str) -> dict:
    """Create a bulleted list item block."""
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": make_rich_text(content)},
    }


def make_numbered_list_block(content: str) -> dict:
    """Create a numbered list item block."""
    return {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {"rich_text": make_rich_text(content)},
    }


def make_code_block(content: str, language: str = "plain text") -> dict:
    """Create a code block."""
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": make_rich_text(content),
            "language": language,
        },
    }


def make_divider_block() -> dict:
    """Create a divider block."""
    return {"object": "block", "type": "divider", "divider": {}}

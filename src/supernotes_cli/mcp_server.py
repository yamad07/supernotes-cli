from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from supernotes_cli.client import SupernotesClient
from supernotes_cli.config import get_api_key

mcp = FastMCP("supernotes")


def _client() -> SupernotesClient:
    return SupernotesClient(get_api_key())


@mcp.tool()
async def supernotes_get_card(card_id: str) -> str:
    """Get a Supernotes card by ID. Returns the card name, content, tags, and metadata."""
    async with _client() as client:
        card = await client.get_card(card_id)
        return card.format_text()


@mcp.tool()
async def supernotes_search_cards(
    query: str = "",
    limit: int = 20,
    parent_id: str = "",
    visibility: str = "",
) -> str:
    """Search Supernotes cards. Returns matching cards with their IDs, names, and content.

    Args:
        query: Search text to filter cards. Leave empty to list recent cards.
        limit: Maximum number of cards to return (default 20).
        parent_id: Filter by parent card ID. Leave empty for all cards.
        visibility: Filter by visibility. "priority" (shown in Outline), "visible" (Noteboard only), "invisible" (hidden). Leave empty for all.
    """
    vis_map = {"priority": 1, "visible": 0, "invisible": -1}
    vis_value = vis_map.get(visibility) if visibility else None
    async with _client() as client:
        cards = await client.search_cards(
            query=query or None,
            limit=limit,
            parent_id=parent_id or None,
            visibility=vis_value,
        )
        if not cards:
            return "No cards found."
        return "\n---\n".join(card.format_text() for card in cards)


@mcp.tool()
async def supernotes_get_collections() -> str:
    """List all Supernotes collections owned by the user, with their IDs, names, and filters."""
    async with _client() as client:
        items = await client.get_collections()
        if not items:
            return "No collections found."
        return "\n---\n".join(c.format_text() for c in items)


@mcp.tool()
async def supernotes_create_card(
    name: str,
    markup: str = "",
    tags: list[str] | None = None,
    color: str | None = None,
    parent_id: str | None = None,
) -> str:
    """Create a new Supernotes card.

    Args:
        name: Card title (required).
        markup: Card content in markdown format.
        tags: List of tags for the card.
        color: Card color (blue, green, orange, pink, purple, red, yellow).
        parent_id: Parent card ID to nest this card under.
    """
    parent_ids = [parent_id] if parent_id else None
    async with _client() as client:
        card = await client.create_card(
            name=name, markup=markup, tags=tags,
            color=color, parent_ids=parent_ids,
        )
        return card.format_text()


@mcp.tool()
async def supernotes_update_card(
    card_id: str,
    name: str | None = None,
    markup: str | None = None,
    tags: list[str] | None = None,
    color: str | None = None,
) -> str:
    """Update an existing Supernotes card.

    Args:
        card_id: ID of the card to update (required).
        name: New card title.
        markup: New card content in markdown.
        tags: New list of tags (replaces existing tags).
        color: New card color.
    """
    async with _client() as client:
        card = await client.update_card(
            card_id=card_id, name=name, markup=markup,
            tags=tags, color=color,
        )
        return card.format_text()


@mcp.tool()
async def supernotes_append_to_card(card_id: str, content: str) -> str:
    """Append markdown content to an existing Supernotes card.

    Args:
        card_id: ID of the card to append to (required).
        content: Markdown content to append.
    """
    async with _client() as client:
        card = await client.append_to_card(card_id, content)
        return card.format_text()


@mcp.tool()
async def supernotes_delete_cards(card_ids: list[str]) -> str:
    """Permanently delete Supernotes cards. This action is irreversible.

    Args:
        card_ids: List of card IDs to delete.
    """
    async with _client() as client:
        result = await client.delete_cards(card_ids)
        lines = [f"{cid}: {'deleted' if status == 200 else f'error ({status})'}" for cid, status in result.items()]
        return "\n".join(lines)

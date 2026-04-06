from __future__ import annotations

import asyncio
import json
import sys

import click

from supernotes_cli.client import SupernotesClient
from supernotes_cli.config import get_api_key, save_api_key


def _run(coro):
    return asyncio.run(coro)


def _get_client() -> SupernotesClient:
    return SupernotesClient(get_api_key())


@click.group()
@click.option("--json-output", "json_out", is_flag=True, help="Output as JSON")
@click.pass_context
def main(ctx, json_out: bool):
    """Supernotes CLI - Manage your cards from the command line."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_out


def _output(ctx, card):
    if ctx.obj.get("json"):
        click.echo(json.dumps(card.model_dump(), indent=2, default=str))
    else:
        click.echo(card.format_text())


def _output_list(ctx, cards):
    if ctx.obj.get("json"):
        click.echo(json.dumps([c.model_dump() for c in cards], indent=2, default=str))
    else:
        for i, card in enumerate(cards):
            if i > 0:
                click.echo("---")
            click.echo(card.format_text())


@main.command()
@click.argument("card_id")
@click.pass_context
def get(ctx, card_id: str):
    """Get a card by ID."""
    async def _do():
        async with _get_client() as client:
            return await client.get_card(card_id)
    _output(ctx, _run(_do()))


@main.command()
@click.option("--query", "-q", default=None, help="Search query")
@click.option("--limit", "-l", default=20, help="Max results")
@click.option("--parent", "-p", default=None, help="Parent card ID")
@click.option("--visibility", "-v", default=None, type=click.Choice(["priority", "visible", "invisible"]), help="Filter by visibility")
@click.pass_context
def search(ctx, query: str | None, limit: int, parent: str | None, visibility: str | None):
    """Search cards."""
    vis_map = {"priority": 1, "visible": 0, "invisible": -1}
    vis_value = vis_map[visibility] if visibility else None

    async def _do():
        async with _get_client() as client:
            return await client.search_cards(query=query, limit=limit, parent_id=parent, visibility=vis_value)
    _output_list(ctx, _run(_do()))


@main.command()
@click.argument("name")
@click.option("--markup", "-m", default="", help="Card content (markdown)")
@click.option("--tags", "-t", default=None, help="Comma-separated tags")
@click.option("--color", "-c", default=None, help="Card color")
@click.option("--parent", "-p", default=None, help="Parent card ID")
@click.option("--icon", default=None, help="Card icon")
@click.pass_context
def create(ctx, name: str, markup: str, tags: str | None, color: str | None, parent: str | None, icon: str | None):
    """Create a new card."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    parent_ids = [parent] if parent else None

    async def _do():
        async with _get_client() as client:
            return await client.create_card(
                name=name, markup=markup, tags=tag_list,
                color=color, parent_ids=parent_ids, icon=icon,
            )
    _output(ctx, _run(_do()))


@main.command()
@click.argument("card_id")
@click.option("--name", "-n", default=None, help="New name")
@click.option("--markup", "-m", default=None, help="New content")
@click.option("--tags", "-t", default=None, help="Comma-separated tags")
@click.option("--color", "-c", default=None, help="New color")
@click.option("--icon", default=None, help="New icon")
@click.pass_context
def update(ctx, card_id: str, name: str | None, markup: str | None, tags: str | None, color: str | None, icon: str | None):
    """Update a card."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    async def _do():
        async with _get_client() as client:
            return await client.update_card(
                card_id=card_id, name=name, markup=markup,
                tags=tag_list, color=color, icon=icon,
            )
    _output(ctx, _run(_do()))


@main.command()
@click.argument("card_id")
@click.argument("content")
@click.pass_context
def append(ctx, card_id: str, content: str):
    """Append content to a card."""
    async def _do():
        async with _get_client() as client:
            return await client.append_to_card(card_id, content)
    _output(ctx, _run(_do()))


@main.command()
@click.argument("card_ids", nargs=-1, required=True)
@click.pass_context
def delete(ctx, card_ids: tuple[str, ...]):
    """Permanently delete cards."""
    async def _do():
        async with _get_client() as client:
            return await client.delete_cards(list(card_ids))

    result = _run(_do())
    if ctx.obj.get("json"):
        click.echo(json.dumps(result, indent=2))
    else:
        for cid, status in result.items():
            click.echo(f"{cid}: {status}")


@main.command()
@click.argument("card_ids", nargs=-1, required=True)
@click.pass_context
def remove(ctx, card_ids: tuple[str, ...]):
    """Remove cards for current user."""
    async def _do():
        async with _get_client() as client:
            return await client.remove_cards(list(card_ids))

    result = _run(_do())
    if ctx.obj.get("json"):
        click.echo(json.dumps(result, indent=2))
    else:
        for cid, status in result.items():
            click.echo(f"{cid}: {status}")


@main.group()
def config():
    """Manage configuration."""
    pass


@config.command("set-key")
def set_key():
    """Set your Supernotes API key."""
    key = click.prompt("Enter your Supernotes API key", hide_input=True)
    save_api_key(key)
    click.echo("API key saved.")


@main.command()
def mcp():
    """Start the MCP server (stdio transport)."""
    from supernotes_cli.mcp_server import mcp as mcp_app
    mcp_app.run(transport="stdio")


if __name__ == "__main__":
    main()

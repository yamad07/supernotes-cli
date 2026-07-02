from __future__ import annotations

from typing import Any

import httpx

from supernotes_cli.models import CardData, CardMembership, CardResponse

BASE_URL = "https://api.supernotes.app"


class SupernotesClient:
    def __init__(self, api_key: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"Api-Key": api_key},
            timeout=30.0,
        )

    async def __aenter__(self) -> SupernotesClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._client.aclose()

    def _parse_card(self, data: dict) -> CardResponse:
        return CardResponse(
            data=CardData(**data["data"]),
            membership=CardMembership(**data["membership"]) if data.get("membership") else None,
            backlinks=data.get("backlinks", []),
            parents=data.get("parents", {}),
        )

    def _extract_card_from_multi_status(self, result: Any, card_id: str | None = None) -> CardResponse:
        """Extract a card from a 207 Multi-Status response.

        The API returns a list of: {"success": bool, "card_id": str, "status_code": int, "payload": {card data}}
        """
        if isinstance(result, list):
            for item in result:
                if isinstance(item, dict) and item.get("success") and "payload" in item:
                    return self._parse_card(item["payload"])
            # Check for error in response
            for item in result:
                if isinstance(item, dict) and not item.get("success"):
                    raise RuntimeError(f"API error: {item}")
        elif isinstance(result, dict):
            if card_id and card_id in result:
                card_data = result[card_id]
            else:
                _, card_data = next(iter(result.items()))
            if isinstance(card_data, dict) and "data" in card_data:
                return self._parse_card(card_data)
        raise RuntimeError(f"Unexpected API response: {result}")

    async def get_card(self, card_id: str) -> CardResponse:
        resp = await self._client.get(f"/v1/cards/{card_id}")
        resp.raise_for_status()
        return self._parse_card(resp.json())

    async def search_cards(
        self,
        query: str | None = None,
        limit: int = 20,
        parent_id: str | None = None,
        visibility: int | None = None,
    ) -> list[CardResponse]:
        body: dict[str, Any] = {
            "limit": limit,
            "include_membership_statuses": [0, 1, 2],
        }
        if query:
            body["search"] = query
        if parent_id:
            body["parent_id"] = parent_id
        if visibility is not None:
            body["filter_group"] = {
                "type": "group",
                "op": "and",
                "filters": [
                    {"type": "visibility", "op": "equals", "arg": visibility},
                ],
            }

        resp = await self._client.post("/v1/cards/get/select", json=body)
        resp.raise_for_status()
        result = resp.json()
        return [self._parse_card(v) for v in result.values()]

    async def create_card(
        self,
        name: str,
        markup: str = "",
        tags: list[str] | None = None,
        color: str | None = None,
        parent_ids: list[str] | None = None,
        icon: str | None = None,
    ) -> CardResponse:
        body: dict[str, Any] = {"name": name, "markup": markup}
        if tags:
            body["tags"] = tags
        if color:
            body["color"] = color
        if parent_ids:
            body["parent_ids"] = parent_ids
        if icon:
            body["icon"] = icon

        resp = await self._client.post("/v1/cards/simple", json=body)
        resp.raise_for_status()
        return self._extract_card_from_multi_status(resp.json())

    async def update_card(
        self,
        card_id: str,
        name: str | None = None,
        markup: str | None = None,
        tags: list[str] | None = None,
        color: str | None = None,
        icon: str | None = None,
    ) -> CardResponse:
        patch: dict[str, Any] = {}
        if name is not None:
            patch["name"] = name
        if markup is not None:
            patch["markup"] = markup
        if tags is not None:
            patch["tags"] = tags
        if color is not None:
            patch["color"] = color
        if icon is not None:
            patch["icon"] = icon

        if not patch:
            raise ValueError("No fields to update")

        resp = await self._client.patch("/v1/cards", json={card_id: {"data": patch}})
        resp.raise_for_status()
        return self._extract_card_from_multi_status(resp.json(), card_id)

    async def append_to_card(self, card_id: str, content: str) -> CardResponse:
        resp = await self._client.put(
            f"/v1/cards/simple/{card_id}/append",
            content=content,
            headers={"Content-Type": "text/plain"},
        )
        resp.raise_for_status()
        return self._extract_card_from_multi_status(resp.json(), card_id)

    async def _move_cards_to_junk(self, card_ids: list[str]) -> None:
        """Move cards to Junk before delete/remove.

        Supernotes requires a card membership to be disabled (status -2) before
        the card can be removed or permanently deleted. The /v1/cards PATCH
        endpoint expects each patch to be split into top-level "data" and/or
        "membership" sections.
        """
        if not card_ids:
            return

        resp = await self._client.patch(
            "/v1/cards",
            json={card_id: {"membership": {"status": -2}} for card_id in card_ids},
        )
        resp.raise_for_status()

    async def delete_cards(self, card_ids: list[str]) -> dict[str, int]:
        await self._move_cards_to_junk(card_ids)
        resp = await self._client.post("/v1/cards/delete", json=card_ids)
        resp.raise_for_status()
        return resp.json()

    async def remove_cards(self, card_ids: list[str]) -> dict[str, int]:
        await self._move_cards_to_junk(card_ids)
        resp = await self._client.post("/v1/cards/remove", json=card_ids)
        resp.raise_for_status()
        return resp.json()

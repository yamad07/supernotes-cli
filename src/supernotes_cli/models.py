from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CardData(BaseModel):
    id: str
    owner_id: str
    name: str
    markup: str
    html: str = ""
    icon: str | None = None
    tags: list[str] = []
    color: str | None = None
    created_when: datetime | None = None
    modified_when: datetime | None = None
    meta: dict | None = None
    daily_date: str | None = None
    likes: int = 0
    comment_count: int = 0
    member_count: int = 0


class CardMembership(BaseModel):
    id: str | None = None
    status: int | None = None
    visibility: int | None = None


class CollectionResponse(BaseModel):
    id: str
    spec: dict
    view: dict | None = None
    order: str | None = None
    created_when: datetime | None = None
    modified_when: datetime | None = None

    @property
    def name(self) -> str:
        # spec is either defined (name/description/...) or a reference to a
        # preconfigured collection (pre_id only)
        return self.spec.get("name") or self.spec.get("pre_id") or ""

    def format_text(self) -> str:
        lines = [
            f"# {self.name}",
            f"ID: {self.id}",
        ]
        if self.spec.get("pre_id"):
            lines.append(f"Preconfigured: {self.spec['pre_id']}")
        if self.spec.get("description"):
            lines.append(f"Description: {self.spec['description']}")
        if self.spec.get("icon"):
            lines.append(f"Icon: {self.spec['icon']}")
        if self.spec.get("color"):
            lines.append(f"Color: {self.spec['color']}")
        if self.created_when:
            lines.append(f"Created: {self.created_when}")
        if self.modified_when:
            lines.append(f"Modified: {self.modified_when}")
        return "\n".join(lines)


class CardResponse(BaseModel):
    data: CardData
    membership: CardMembership | None = None
    backlinks: list[str] = []
    parents: dict = {}

    def format_text(self) -> str:
        lines = [
            f"# {self.data.name}",
            f"ID: {self.data.id}",
        ]
        if self.data.tags:
            lines.append(f"Tags: {', '.join(self.data.tags)}")
        if self.data.color:
            lines.append(f"Color: {self.data.color}")
        if self.data.created_when:
            lines.append(f"Created: {self.data.created_when}")
        if self.data.modified_when:
            lines.append(f"Modified: {self.data.modified_when}")
        lines.append("")
        lines.append(self.data.markup)
        return "\n".join(lines)

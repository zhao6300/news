from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Sequence


Slug = str


class CategoryGroup(StrEnum):
    AI = "ai"
    NEWS = "news"
    TECH = "tech"
    FINANCE = "finance"
    MODELS = "models"
    REVIEWS = "reviews"


@dataclass(frozen=True, slots=True)
class Article:
    id: int
    title: str
    url: str
    summary: str
    tags: tuple[str, ...]
    source: str
    category_id: CategoryGroup
    rank: int
    published_at: datetime

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> Article:
        return cls(
            id=int(record["id"]),
            title=str(record["title"]),
            url=str(record["url"]),
            summary=str(record["summary"]),
            tags=tuple(str(tag) for tag in record["tags"]),
            source=str(record["source"]),
            category_id=CategoryGroup(str(record["category_id"])),
            rank=int(record["rank"]),
            published_at=datetime.fromisoformat(str(record["published_at"])),
        )

    @property
    def published_at_display(self) -> str:
        return self.published_at.strftime("%Y-%m-%d")


@dataclass(frozen=True, slots=True)
class Category:
    id: int
    slug: Slug
    label: str

    @property
    def url_path(self) -> str:
        return f"/category/{self.slug}"


@dataclass(frozen=True, slots=True)
class PlatformExtension:
    slug: str
    label: str
    entries: Sequence[Article]

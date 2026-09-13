from __future__ import annotations

from datetime import UTC, date, datetime, time
from typing import Sequence

from scaffold import CategoryGroup, Article, PlatformExtension


def _published_at(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=UTC)


def builtin_collections() -> Sequence[PlatformExtension]:
    entries = [
        Article(
            id=1,
            title="AI Information Discovery",
            url="https://example.com/ai",
            summary="Track the development of AI information infrastructure.",
            tags=("AI", "Information Architecture"),
            source="Example Research",
            category_id=CategoryGroup.AI,
            rank=1,
            published_at=_published_at(date(2026, 1, 5)),
        ),
        Article(
            id=5,
            title="AI Industry News Roundup",
            url="https://example.com/news",
            summary="Daily coverage of releases, funding, policy, and research milestones.",
            tags=("News", "AI", "Industry"),
            source="Newsroom",
            category_id=CategoryGroup.NEWS,
            rank=1,
            published_at=_published_at(date(2026, 9, 10)),
        ),
        Article(
            id=2,
            title="Technology Trends Digest",
            url="https://example.com/tech",
            summary="A concise digest of applied technology trends.",
            tags=("Technology", "Engineering"),
            source="Digest",
            category_id=CategoryGroup.TECH,
            rank=1,
            published_at=_published_at(date(2026, 1, 6)),
        ),
        Article(
            id=3,
            title="Model Evaluation Notes",
            url="https://example.com/models",
            summary="Notes and results from ongoing model evaluation.",
            tags=("Models", "Evaluation"),
            source="Model Notes",
            category_id=CategoryGroup.MODELS,
            rank=1,
            published_at=_published_at(date(2026, 1, 7)),
        ),
        Article(
            id=4,
            title="Product Review Roundup",
            url="https://example.com/reviews",
            summary="Short reviews from the information platform.",
            tags=("Reviews", "Products"),
            source="Editorial",
            category_id=CategoryGroup.REVIEWS,
            rank=1,
            published_at=_published_at(date(2026, 1, 8)),
        ),
    ]
    return [PlatformExtension(slug="builtin", label="Builtin", entries=entries)]

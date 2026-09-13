from __future__ import annotations

from datetime import UTC, datetime

from scaffold import Article, CategoryGroup
from storage import RepositoryLayer
from sqlite_store import SQLiteArticleLayer


def _article(article_id: int, rank: int = 1) -> Article:
    return Article(
        id=article_id,
        title=f"Article {article_id}",
        url=f"https://example.com/{article_id}",
        summary="Example summary.",
        tags=("technology",),
        source="Example",
        category_id=CategoryGroup.TECH,
        rank=rank,
        published_at=datetime(2026, 1, article_id, tzinfo=UTC),
    )

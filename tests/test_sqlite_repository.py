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


def test_sqlite_category_counts_are_aggregated_in_one_query(tmp_path):
    repository = SQLiteArticleLayer(tmp_path / "counts.db")
    repository.add(_article(1))
    repository.add(
        Article(
            id=2,
            title="Example news",
            url="https://example.com/news",
            summary="Example summary.",
            tags=("news",),
            source="Example",
            category_id=CategoryGroup.NEWS,
            rank=1,
            published_at=datetime(2026, 1, 2, tzinfo=UTC),
        )
    )

    counts = repository.counts_by_category()

    assert counts == {category: 0 for category in CategoryGroup} | {
        CategoryGroup.TECH: 1,
        CategoryGroup.NEWS: 1,
    }

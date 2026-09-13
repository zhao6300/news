from __future__ import annotations

from datetime import UTC, datetime

from scaffold import Article, CategoryGroup
from storage import InMemoryRepositoryLayer, RepositoryLayer


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


def test_repository_interface_covers_add_get_remove_and_page():
    for method in ("add", "get", "remove", "list_page"):
        assert hasattr(RepositoryLayer, method)


def test_refreshed_article_moves_content_between_categories():
    repository = InMemoryRepositoryLayer()
    repository.add(_article(1))

    repository.update(
        Article(
            1,
            "Article 1",
            "https://example.com/1",
            "Updated summary.",
            ("news",),
            "Example",
            CategoryGroup.NEWS,
            1,
            _article(1).published_at,
        )
    )

    assert repository.get(1).summary == "Updated summary."
    counts = repository.counts_by_category()
    assert counts[CategoryGroup.TECH] == 0
    assert counts[CategoryGroup.NEWS] == 1

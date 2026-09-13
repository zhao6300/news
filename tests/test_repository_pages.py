from __future__ import annotations

from datetime import UTC, datetime

from scaffold import Article, CategoryGroup
from storage import InMemoryRepositoryLayer


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


def test_repository_pages_return_correct_slice_and_total():
    repository = InMemoryRepositoryLayer()
    for article_id, rank in ((1, 5), (2, 3), (3, 1), (4, 4), (5, 2)):
        repository.register(_article(article_id, rank))

    page = repository.list_page(CategoryGroup.TECH, page=2, page_size=2)

    assert [entry.id for entry in page.items] == [2, 5]
    assert page.total == 5

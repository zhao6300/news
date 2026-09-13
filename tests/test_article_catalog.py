from __future__ import annotations

from datetime import UTC, datetime

from extensions.builtin import builtin_collections
from scaffold import Article, CategoryGroup
from services import InMemoryPlatformService
from storage import InMemoryRepositoryLayer


def test_service_paginates_articles_from_repository():
    repository = InMemoryRepositoryLayer()
    service = InMemoryPlatformService(builtin_collections())
    service.repository = repository

    article = Article(
        id=0,
        title="Example",
        url="https://example.com",
        summary="Example summary.",
        tags=("example",),
        source="Example",
        category_id=CategoryGroup.TECH,
        rank=1,
        published_at=datetime(2026, 1, 8, tzinfo=UTC),
    )
    repository.register(article)

    assert [entry.title for entry in service.list_articles(CategoryGroup.TECH)] == ["Example"]
    assert service.get_article(1) == repository.get(1)

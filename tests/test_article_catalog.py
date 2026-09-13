from __future__ import annotations

import pytest

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

    page = service.list_articles(CategoryGroup.TECH)
    assert [entry.title for entry in page.items] == ["Example"]
    assert page.total == 1
    assert service.get_article(1) == repository.get(1)


def test_article_record_repository_preserves_article_fields():
    record = {
        "id": 42,
        "title": "Record round-trip",
        "url": "https://example.com/42",
        "summary": "Structured record.",
        "tags": ["Model", "Evaluation"],
        "source": "Test Source",
        "category_id": "models",
        "rank": 2,
        "published_at": "2026-02-01T09:00:00+00:00",
    }

    article = Article.from_record(record)

    assert article.category_id == CategoryGroup.MODELS
    assert article.tags == ("Model", "Evaluation")
    assert article.published_at == datetime(2026, 2, 1, 9, tzinfo=UTC)


def test_capped_page_size_rejects_invalid_pagination():
    service = InMemoryPlatformService(builtin_collections())
    service.repository = InMemoryRepositoryLayer()

    with pytest.raises(ValueError, match="Page must be positive"):
        service.list_articles(CategoryGroup.TECH, page=0)
    with pytest.raises(ValueError, match="Page size must be positive"):
        service.list_articles(CategoryGroup.TECH, page_size=0)
    with pytest.raises(ValueError, match="not exceed 50"):
        service.list_articles(CategoryGroup.TECH, page_size=51)

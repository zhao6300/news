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


def test_service_filters_articles_by_query_source_and_category():
    repository = InMemoryRepositoryLayer()
    service = InMemoryPlatformService(builtin_collections())
    service.repository = repository
    articles = [
        Article(
            id=1,
            title="Open model evaluation",
            url="https://example.com/open-model",
            summary="A model focused report.",
            tags=("models",),
            source="Model Notes",
            category_id=CategoryGroup.MODELS,
            rank=2,
            published_at=datetime(2026, 1, 2, tzinfo=UTC),
        ),
        Article(
            id=2,
            title="Technology digest",
            url="https://example.com/tech",
            summary="A technology focused report.",
            tags=("technology",),
            source="Tech Digest",
            category_id=CategoryGroup.TECH,
            rank=3,
            published_at=datetime(2026, 1, 3, tzinfo=UTC),
        ),
        Article(
            id=3,
            title="Finance briefing",
            url="https://example.com/finance",
            summary="A finance focused report.",
            tags=("finance",),
            source="Tech Digest",
            category_id=CategoryGroup.FINANCE,
            rank=1,
            published_at=datetime(2026, 1, 1, tzinfo=UTC),
        ),
    ]
    for article in articles:
        repository.register(article)

    assert [article.id for article in service.list_articles(query="technology").items] == [2]
    assert [article.id for article in service.list_articles(source="Tech Digest").items] == [2, 3]
    assert [article.id for article in service.list_articles(CategoryGroup.MODELS).items] == [1]
    assert service.list_articles().total == 3


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

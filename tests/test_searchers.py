from __future__ import annotations

from searchers import InMemorySearchEngine
from datetime import UTC, datetime
from scaffold import Article
from scaffold import CategoryGroup


def _article(article_id: int, category: CategoryGroup, source: str = "Example") -> Article:
    return Article(
        id=article_id,
        title=f"Example {category.value}",
        url=f"https://example.com/{article_id}",
        summary="Example summary.",
        tags=(category.value,),
        source=source,
        category_id=category,
        rank=1,
        published_at=datetime(2026, 1, article_id, tzinfo=UTC),
    )


def test_search_engine_filters_by_selected_category():
    articles = [
        _article(1, CategoryGroup.TECH),
        _article(2, CategoryGroup.AI),
    ]
    engine = InMemorySearchEngine(articles)

    result = engine.search("example", category=CategoryGroup.AI)

    assert [article.id for article in result.items] == [2]
    assert result.total == 1


def test_search_engine_filters_articles_by_source():
    articles = [
        _article(1, CategoryGroup.TECH, source="AI Digest"),
        _article(2, CategoryGroup.AI, source="Other Source"),
    ]
    engine = InMemorySearchEngine(articles)

    result = engine.search("example", source="AI Digest")

    assert [article.id for article in result.items] == [1]
    assert result.total == 1


def test_search_engine_ignores_empty_source_filter():
    articles = [
        _article(1, CategoryGroup.TECH, source="AI Digest"),
        _article(2, CategoryGroup.AI, source="AI Digest"),
    ]
    engine = InMemorySearchEngine(articles)

    result = engine.search("example", source=None)

    assert [article.id for article in result.items] == [1, 2]
    assert result.total == 2

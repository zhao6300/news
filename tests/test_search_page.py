from __future__ import annotations

from app import render_article_items, render_search_results
from storage import Page
from scaffold import Article, CategoryGroup
from datetime import UTC, datetime


def test_search_results_show_query_and_no_match():
    empty_result = Page([], page=1, page_size=10, total=0)

    assert "No matching content" in render_search_results("Example", empty_result)
    assert "0 matching pages" in render_search_results("Example", empty_result)


def _article(article_id: int, category: CategoryGroup = CategoryGroup.TECH) -> Article:
    return Article(
        id=article_id,
        title=f"Article {article_id}",
        url=f"https://example.com/{article_id}",
        summary="Example summary.",
        tags=("technology",),
        source="Example",
        category_id=category,
        rank=1,
        published_at=datetime(2026, 1, article_id, tzinfo=UTC),
    )

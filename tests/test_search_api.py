from __future__ import annotations

from datetime import UTC, datetime

from app import article_search_payload, render_search_page
from scaffold import Article
from scaffold import CategoryGroup
from storage import Page


def test_search_api_payload_carries_complete_ingested_metadata():
    article = Article(
        1,
        "Sample article",
        "https://example.com/sample",
        "Sample summary.",
        ("example",),
        "Example",
        CategoryGroup.TECH,
        1,
        datetime(2026, 1, 1, tzinfo=UTC),
    )

    payload = article_search_payload(article)

    assert payload["source"] == "Example"
    assert payload["url"] == "https://example.com/sample"
    assert payload["published_at"] == "2026-01-01T00:00:00+00:00"


def test_search_page_renders_matches_without_articles():
    result = Page([], page=1, page_size=10, total=0)

    assert "Search:" not in render_search_page("Example", f"<p>{result.total}</p>")

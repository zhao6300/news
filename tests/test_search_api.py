from __future__ import annotations

from app import render_search_page
from storage import Page


def test_search_page_renders_matches_without_articles():
    result = Page([], page=1, page_size=10, total=0)

    assert "Search" not in render_search_page("Example", f"<p>{result.total}</p>")

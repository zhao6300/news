from __future__ import annotations

from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from auth import Account, Address, Registration, demo_account_manager
from extensions.builtin import builtin_collections
from app import (
    render_article_items,
    render_search_results,
    render_article_tags,
    render_article_page,
)
from app import render_search_pagination
from storage import Page
from scaffold import Article, CategoryGroup
from datetime import UTC, datetime
from app import PortalHandler
from searchers import InMemorySearchEngine
from services import InMemoryPlatformService
from sessions import SessionManager


def test_search_results_show_query_and_no_match():
    empty_result = Page([], page=1, page_size=10, total=0)

    assert "No matching content" in render_search_results("Example", empty_result)
    assert "0 matching pages" in render_search_results("Example", empty_result)


def test_article_items_render_semantic_cards_with_source_and_category():
    html = render_article_items([_article(1)])

    assert "<article class='article-card'>" in html
    assert "/article/1" in html
    assert "Article 1" in html
    assert "Example · Tech" in html
    assert "2026-01-01" in html


def test_search_pagination_preserves_query_filters_and_bounds():
    result = Page([], page=2, page_size=10, total=31)

    pagination = render_search_pagination("models", result, CategoryGroup.MODELS)

    assert "Page 2 of 4" in pagination
    assert "/search?q=models&amp;category=models&amp;page=1&amp;page_size=10" in pagination
    assert "/search?q=models&amp;category=models&amp;page=3&amp;page_size=10" in pagination
    assert "/search?q=models&amp;category=models&amp;page=4&amp;page_size=10" in pagination


def test_single_page_search_hides_pagination():
    result = Page([], page=1, page_size=10, total=7)

    html = render_search_results("models", result, CategoryGroup.MODELS)

    assert "Page 1 of " not in html


def test_article_tags_render_individually():
    article = _article(1)

    html = render_article_tags(article)

    assert "<span class='tag'>technology</span>" in html


def test_article_detail_shows_publish_date():
    article = _article(1)

    html = render_article_page(article)

    assert "2026-01-01" in html
    assert "Example · Tech" in html


def test_article_items_render_collected_tags():
    article = _article(1)

    html = render_article_items([article])

    assert "<span class='tag'>technology</span>" in html


def test_authenticated_search_page_accepts_category_filter():
    service = InMemoryPlatformService(builtin_collections())
    session_manager = SessionManager()
    cookie = (
        "portal_session="
        + session_manager.create(
            Account(
                1,
                "member@example.com",
                "hash",
                "salt",
                address=Address(),
                profile=Registration("standard", "standard"),
            )
        ).token
    )
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(
            service,
            demo_account_manager(),
            session_manager,
            InMemorySearchEngine(builtin_collections()[0].entries),
            *args,
            **kwargs,
        ),
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        query = urlencode({"q": "Example", "category": "ai"})
        with urlopen(
            Request(
                f"http://127.0.0.1:{server.server_port}/search?{query}",
                headers={"Cookie": cookie},
            )
        ) as response:
            assert "aria-current='page'" in response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_authenticated_search_page_shows_page_two():
    service = InMemoryPlatformService(builtin_collections())
    session_manager = SessionManager()
    cookie = (
        "portal_session="
        + session_manager.create(
            Account(
                1,
                "member@example.com",
                "hash",
                "salt",
                address=Address(),
                profile=Registration("standard", "standard"),
            )
        ).token
    )
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(
            service,
            demo_account_manager(),
            session_manager,
            InMemorySearchEngine(builtin_collections()[0].entries),
            *args,
            **kwargs,
        ),
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        query = urlencode({"q": "AI", "page_size": 1, "page": 2})
        with urlopen(
            Request(
                f"http://127.0.0.1:{server.server_port}/search?{query}",
                headers={"Cookie": cookie},
            )
        ) as response:
            payload = response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_search_results_keep_source_filter_in_pagination():
    result = Page([], page=1, page_size=10, total=20)

    html = render_search_results("example", result, None, "AI Digest")

    assert "source=AI+Digest" in html


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

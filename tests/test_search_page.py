from __future__ import annotations

from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from auth import Account, demo_account_manager
from extensions.builtin import builtin_collections
from app import render_article_items, render_search_results
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

from __future__ import annotations

import threading
from datetime import UTC, datetime
from json import loads
from urllib.parse import urlencode
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen

from extensions.builtin import builtin_collections
from app import (
    PortalHandler,
    render_article_items,
    render_extension_section,
    render_extension_view,
    render_login_form,
    render_navigation,
    render_top_bar,
)
from auth import AccountManager, demo_account_manager, install_logged_in_cookie
from connectors import IngestionReport
from sessions import SessionManager
from searchers import InMemorySearchEngine
from services import InMemoryPlatformService
from scaffold import Article
from scaffold import CategoryGroup
from storage import InMemoryRepositoryLayer


def _article(article_id: int, category: CategoryGroup):
    return Article(
        id=article_id,
        title=f"Example {article_id}",
        url="https://example.com",
        summary="Example summary.",
        tags=("example",),
        source="Example",
        category_id=category,
        rank=1,
        published_at=datetime(2026, 1, 8, tzinfo=UTC),
    )
def test_extension_sections_are_rendered_through_service():
    service = InMemoryPlatformService(builtin_collections())
    builtin = service.get_extension("builtin")

    assert "News Intelligence Platform" not in render_extension_section(builtin)


def test_health_endpoint_is_api_reachable():
    service = InMemoryPlatformService(builtin_collections())
    account_manager = AccountManager(())
    session_manager = SessionManager()
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(service, account_manager, session_manager, InMemorySearchEngine([]), *args, **kwargs),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/health") as response:
            assert response.status == 200
            assert response.headers["Content-Type"] == "application/json"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_ingestion_endpoint_reports_job_status():
    reports = (
        IngestionReport("builtin", "Builtin", 5),
        IngestionReport("broken", "Broken", 0, "RuntimeError('source unavailable')"),
    )
    service = InMemoryPlatformService(builtin_collections())
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(
            service,
            AccountManager(()),
            SessionManager(),
            InMemorySearchEngine([]),
            ingestion_reports=reports,
            *args,
            **kwargs,
        ),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/api/ingestion") as response:
            assert response.status == 200
            payload = loads(response.read().decode("utf-8"))
        assert payload["status"] == "degraded"
        assert payload["jobs"][0]["item_count"] == 5
        assert "source unavailable" in payload["jobs"][1]["error"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_category_page_is_resolved_through_service():
    service = InMemoryPlatformService(builtin_collections())
    assert service.get_category("ai") == CategoryGroup.AI
    assert list(service.list_article_categories()) == list(CategoryGroup)


def test_article_detail_is_served():
    repository = InMemoryRepositoryLayer()
    service = InMemoryPlatformService(builtin_collections())
    service.repository = repository
    repository.register(_article(0, CategoryGroup.TECH))

    assert service.get_article(1).title == "Example 0"


def test_category_page_renders_article_results():
    service = InMemoryPlatformService(builtin_collections())
    repository = InMemoryRepositoryLayer()
    service.repository = repository
    repository.register(_article(0, CategoryGroup.TECH))

    assert "Example 0" in render_article_items(service.list_articles(CategoryGroup.TECH).items)


def test_navigation_shows_non_empty_category_counts():
    html = render_navigation({CategoryGroup.TECH: 3})

    assert "/category/tech" in html
    assert "<span>3</span>" in html


def test_extension_view_summarizes_articles_by_category():
    extension = builtin_collections()[0]

    html = render_extension_view(extension)

    assert "Builtin" in html
    assert "6 articles" in html
    assert "New Insight Article" in html
    assert "/category/news" in html


def test_authentication_page_uses_plain_labels():
    html = render_login_form()

    assert "Sign In" in html


def test_home_page_is_served_by_runtime_handler():
    service = InMemoryPlatformService(builtin_collections())
    account_manager = AccountManager(())
    session_manager = SessionManager()
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(service, account_manager, session_manager, InMemorySearchEngine([]), *args, **kwargs),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/") as response:
            assert response.status == 200
            assert "Sign In" in response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_home_page_renders_logout_for_authenticated_cookie():
    session_manager = SessionManager()
    cookie = install_logged_in_cookie(session_manager)
    service = InMemoryPlatformService(builtin_collections())
    service.repository = InMemoryRepositoryLayer()
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(
            service,
            demo_account_manager(),
            session_manager,
            InMemorySearchEngine([]),
            *args,
            **kwargs,
        ),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(
            Request(
                f"http://127.0.0.1:{server.server_port}/",
                headers={"Cookie": cookie},
            )
        ) as response:
            assert response.status == 200
            payload = response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    assert "<a href='/logout'>Log out (member@example.com)</a>" in payload


def test_login_submission_reports_valid_credentials():
    service = InMemoryPlatformService(builtin_collections())
    account_manager = demo_account_manager()
    session_manager = SessionManager()
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(service, account_manager, session_manager, InMemorySearchEngine([]), *args, **kwargs),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    data = urlencode({"email": "member@example.com", "password": "demo-password"}).encode("utf-8")
    try:
        with urlopen(Request(f"http://127.0.0.1:{server.server_port}/login", data=data, method="POST")) as response:
            assert response.status == 200
            assert "News Intelligence Platform" in response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

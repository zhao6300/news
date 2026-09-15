from __future__ import annotations
from urllib.parse import urlparse

import threading
import pytest
from http.client import HTTPConnection
from datetime import UTC, datetime
from json import dumps, loads
from urllib.parse import urlencode
from urllib.error import HTTPError
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
from auth import demo_account_manager as create_demo_account_manager
from app import AccountSettingsHandler
from connectors import IngestionReport
from connectors import RuntimeSourceManager

from tests.test_rss_connector import RSS_XML
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
    assert "<span class='tag'>Research</span>" in render_extension_section(builtin)


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


def test_source_tag_revalidation_accepts_signed_paths():
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


def test_authentication_page_uses_chinese_labels():
    html = render_login_form()

    assert "登录" in html
    assert "邮箱" in html
    assert "密码" in html


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
            assert 'id="view"' in response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_login_failure_keeps_chinese_error():
    service = InMemoryPlatformService(builtin_collections())
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(
            service,
            demo_account_manager(),
                SessionManager(),
            InMemorySearchEngine([]),
            *args,
            **kwargs,
        ),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    data = dumps({"email": "member@example.com", "password": "wrong-password"}).encode("utf-8")
    try:
        try:
            urlopen(Request(f"http://127.0.0.1:{server.server_port}/login", data=data, method="POST"))
        except HTTPError as error:
            assert error.code == 401
            assert "登录失败" in error.read().decode("utf-8")
        else:
            pytest.fail("Invalid login should return HTTP 401.")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_authenticated_login_view_redirects_home():
    session_manager = SessionManager()
    cookie = install_logged_in_cookie(session_manager)
    service = InMemoryPlatformService(builtin_collections())
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
        connection = HTTPConnection("127.0.0.1", server.server_port)
        connection.request("GET", "/login", headers={"Cookie": cookie})
        response = connection.getresponse()
        payload = response.read()
        assert response.status == 303
        assert response.headers["Location"] == "/"
        assert not payload
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_sources_api_reports_existing_connectors():
    service = InMemoryPlatformService(builtin_collections())
    session_manager = SessionManager()
    cookie = install_logged_in_cookie(session_manager)
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(
            service,
            demo_account_manager(),
            session_manager,
            InMemorySearchEngine([]),
            ingestion_reports=(IngestionReport("builtin", "Builtin", 6),),
            *args,
            **kwargs,
        ),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(Request(f"http://127.0.0.1:{server.server_port}/api/sources", headers={"Cookie": cookie})) as response:
            assert response.status == 200
            payload = loads(response.read().decode("utf-8"))

        assert payload["status"] == "ok"
        source = payload["sources"][0]
        assert source["slug"] == "builtin"
        assert source["article_count"] == 6
        assert source["ingestion"]["status"] == "ok"
        assert source["ingestion"]["item_count"] == 6
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_sources_api_adds_linked_source_to_service():
    service = InMemoryPlatformService(builtin_collections())
    service.repository = InMemoryRepositoryLayer()
    search_engine = InMemorySearchEngine([])
    reports = []
    source_manager = RuntimeSourceManager(
        service.repository,
        service,
        search_engine,
        reports,
        fetcher=lambda feed_url, timeout: RSS_XML,
    )
    session_manager = SessionManager()
    cookie = install_logged_in_cookie(session_manager)
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(
            service,
            demo_account_manager(),
            session_manager,
            search_engine,
            ingestion_reports=reports,
            source_manager=source_manager,
            *args,
            **kwargs,
        ),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = Request(
            f"http://127.0.0.1:{server.server_port}/api/sources",
            data=dumps(
                {
                    "label": "研究来源",
                    "category": "models",
                    "feed_url": "https://example.com/research.xml",
                    "limit": 1,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json", "Cookie": cookie},
            method="POST",
        )
        with urlopen(request) as response:
            assert response.status == 200
            payload = loads(response.read().decode("utf-8"))
        assert payload["status"] == "created"
        assert payload["article_count"] == 1
        assert payload["source"]["slug"] == "source"
        assert payload["source"]["label"] == "研究来源"
        assert payload["source"]["ingestion"]["status"] == "ok"

        with urlopen(Request(f"http://127.0.0.1:{server.server_port}/api/sources", headers={"Cookie": cookie})) as response:
            payload = loads(response.read().decode("utf-8"))
        assert [source["slug"] for source in payload["sources"]] == ["builtin", "source"]
        assert payload["sources"][1]["label"] == "研究来源"
        assert payload["sources"][1]["slug"] == "source"
        assert payload["sources"][1]["ingestion"]["item_count"] == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_sources_api_lists_technology_and_finance_presets():
    service = InMemoryPlatformService(builtin_collections())
    service.repository = InMemoryRepositoryLayer()
    source_manager = RuntimeSourceManager(
        service.repository,
        service,
        InMemorySearchEngine([]),
        [],
        fetcher=lambda feed_url, timeout: RSS_XML,
    )
    session_manager = SessionManager()
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(
            service,
            demo_account_manager(),
            session_manager,
            InMemorySearchEngine([]),
                ingestion_reports=[],
                source_manager=source_manager,
                *args,
                **kwargs,
            ),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        cookie = install_logged_in_cookie(session_manager)
        with urlopen(Request(f"http://127.0.0.1:{server.server_port}/api/sources", headers={"Cookie": cookie})) as response:
            payload = loads(response.read().decode("utf-8"))
        option_map = {option["id"]: option for option in payload["source_options"]}
        assert option_map["tech-hacker-news"]["category"] == "tech"
        assert option_map["finance-cnbc"]["category"] == "finance"
        assert len(option_map) == 12
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_sources_api_rejects_missing_fields():
    service = InMemoryPlatformService(builtin_collections())
    service.repository = InMemoryRepositoryLayer()
    source_manager = RuntimeSourceManager(
        service.repository,
        service,
        InMemorySearchEngine([]),
        [],
        fetcher=lambda feed_url, timeout: RSS_XML,
    )
    session_manager = SessionManager()
    cookie = install_logged_in_cookie(session_manager)
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(
            service,
            demo_account_manager(),
            session_manager,
            InMemorySearchEngine([]),
            ingestion_reports=[],
            source_manager=source_manager,
            *args,
            **kwargs,
        ),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = Request(
            f"http://127.0.0.1:{server.server_port}/api/sources",
            data=dumps({}).encode("utf-8"),
            headers={"Content-Type": "application/json", "Cookie": cookie},
            method="POST",
        )
        with pytest.raises(HTTPError) as error:
            urlopen(request)
        assert error.value.code == 400
        payload = loads(error.value.read().decode("utf-8"))
        assert payload["message"] == "来源名称长度必须是 1 到 60 个字符。"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_sources_api_add_action_requires_login():
    source_manager = RuntimeSourceManager(
        InMemoryRepositoryLayer(),
        InMemoryPlatformService(()),
        InMemorySearchEngine([]),
        [],
        fetcher=lambda feed_url, timeout: RSS_XML,
    )
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(
            InMemoryPlatformService(builtin_collections()),
            AccountManager(()),
            SessionManager(),
            InMemorySearchEngine([]),
            ingestion_reports=[],
            source_manager=source_manager,
            *args,
            **kwargs,
        ),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = Request(
            f"http://127.0.0.1:{server.server_port}/api/sources",
            data=dumps({"label": "研究", "category": "tech", "feed_url": "https://example.com/feed"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(HTTPError) as error:
            urlopen(request)
        assert error.value.code == 401
        assert loads(error.value.read().decode("utf-8"))["message"] == "请先登录。"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_home_page_renders_authenticated_top_bar():
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


def test_invalid_search_pagination_returns_not_found():
    service = InMemoryPlatformService(builtin_collections())
    session_manager = SessionManager()
    cookie = install_logged_in_cookie(session_manager)
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
        try:
            urlopen(
                Request(
                    f"http://127.0.0.1:{server.server_port}/api/search?q=Example&page=not-number",
                    headers={"Cookie": cookie},
                )
            )
        except HTTPError as error:
            assert error.code == 404
            assert b"404" in error.read()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


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
    data = dumps({"email": "member@example.com", "password": "demo-password"}).encode("utf-8")
    try:
        with urlopen(Request(f"http://127.0.0.1:{server.server_port}/login", data=data, method="POST")) as response:
            assert response.status == 200
            payload = loads(response.read().decode("utf-8"))
            assert payload["status"] == "ok"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

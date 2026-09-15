from __future__ import annotations

import threading
import pytest
from datetime import UTC, datetime
from json import dumps, loads
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import PortalHandler
from auth import AccountManager, demo_account_manager, install_logged_in_cookie
from connectors import IngestionReport
from extensions.builtin import builtin_collections
from scaffold import Article, CategoryGroup
from searchers import InMemorySearchEngine
from services import InMemoryPlatformService
from sessions import SessionManager
from storage import InMemoryRepositoryLayer


PUBLIC_ROOT = Path(__file__).resolve().parents[1] / "frontend"


def start_server(service, account_manager=None, session_manager=None, ingestion_reports=()):
    created_session_manager = session_manager or SessionManager()
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda request, client_address, http_server: PortalHandler(
            service,
            account_manager or AccountManager(()),
            created_session_manager,
            InMemorySearchEngine([]),
            request,
            client_address,
            http_server,
            public_root=PUBLIC_ROOT,
            ingestion_reports=ingestion_reports,
        ),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def read_json(response):
    return loads(response.read().decode("utf-8"))


def test_public_shell_and_static_assets_are_separated():
    service = InMemoryPlatformService(builtin_collections())
    server, thread = start_server(service)
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/") as html_response:
            assert html_response.status == 200
            assert html_response.headers["Content-Type"].startswith("text/html")
            html = html_response.read().decode("utf-8")
            assert '<div id="view"' in html
            assert '<button id="assistant-launcher"' in html
            assert "SSR Home" not in html
            assert "frontend/core/main.js" not in html
            assert "/static/app.js" in html

        with urlopen(f"http://127.0.0.1:{server.server_port}/static/styles.css") as css_response:
            assert css_response.status == 200
            assert css_response.headers["Content-Type"].startswith("text/css")
            assert css_response.headers["Cache-Control"] == "no-store"

        with urlopen(f"http://127.0.0.1:{server.server_port}/static/app.js") as js_response:
            assert js_response.status == 200
            assert js_response.headers["Content-Type"].startswith("text/javascript")
            assert js_response.headers["Cache-Control"] == "no-store"
            frontend_script = js_response.read().decode("utf-8")
            assert "async function api" in frontend_script
            assert 'credentials: "include"' in frontend_script
            assert "renderFilterControls" in frontend_script
            assert "filter-category" in frontend_script
            assert "filter-source" in frontend_script
            assert "articleCards = articles.items.map" in frontend_script
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_source_renderer_tolerates_bootstrap_without_categories():
    frontend_script = (PUBLIC_ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "(source.categories || [])" in frontend_script


def test_public_bootstrap_reports_categories_and_account_state():
    service = InMemoryPlatformService(builtin_collections())
    service.repository = InMemoryRepositoryLayer()
    article = Article(
        id=1,
        title="Example Seeded Article",
        url="https://example.com/article",
        summary="Example summary.",
        tags=("AI",),
        source="Example",
        category_id=CategoryGroup.AI,
        rank=1,
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    service.repository.add(article)
    server, thread = start_server(service)
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/api/bootstrap") as response:
            payload = read_json(response)
        assert payload["account"] is None
        assert [category["slug"] for category in payload["categories"]] == [
            "ai",
            "news",
            "tech",
            "finance",
            "models",
            "reviews",
        ]
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_static_resources_cannot_escape_public_root():
    service = InMemoryPlatformService(builtin_collections())
    server, thread = start_server(service)
    try:
        try:
            urlopen(f"http://127.0.0.1:{server.server_port}/static/../auth.py")
        except HTTPError as error:
            assert error.code == 404
        else:
            pytest.fail("Static assets must remain inside frontend/.")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_json_login_returns_session_cookie():
    service = InMemoryPlatformService(builtin_collections())
    session_manager = SessionManager()
    server, thread = start_server(
        service,
        demo_account_manager(),
    )
    request = Request(
        f"http://127.0.0.1:{server.server_port}/api/login",
        data=dumps({"email": "member@example.com", "password": "demo-password"}).encode("utf-8"),
        method="POST",
    )
    try:
        with urlopen(request) as response:
            assert response.status == 200
            assert read_json(response)["status"] == "ok"
            assert response.headers["Set-Cookie"].startswith("portal_session=")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_article_and_extension_apis_share_service_data():
    service = InMemoryPlatformService(builtin_collections())
    service.repository = InMemoryRepositoryLayer()
    server, thread = start_server(
        service,
        demo_account_manager(),
        ingestion_reports=(IngestionReport("builtin", "Builtin", 6),),
    )
    try:
        seeded_article = Article(
            id=1,
            title="Example Seeded Article",
            url="https://example.com/article",
            summary="Example summary.",
            tags=("AI",),
            source="Example",
            category_id=CategoryGroup.AI,
            rank=1,
            published_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        service.repository.add(seeded_article)
        login_request = Request(
            f"http://127.0.0.1:{server.server_port}/api/login",
            data=dumps({"email": "member@example.com", "password": "demo-password"}).encode("utf-8"),
            method="POST",
        )
        with urlopen(login_request) as login_response:
            cookie = login_response.headers["Set-Cookie"].split(";", maxsplit=1)[0]
        with urlopen(
            Request(
                f"http://127.0.0.1:{server.server_port}/api/articles/1",
                headers={"Cookie": cookie},
            )
        ) as article_response:
            article = read_json(article_response)
        with urlopen(
            Request(
                f"http://127.0.0.1:{server.server_port}/api/extensions/builtin",
                headers={"Cookie": cookie},
            )
        ) as source_response:
            source = read_json(source_response)

        assert article["title"] == seeded_article.title
        assert source["slug"] == "builtin"
        assert source["article_count"] == 6
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

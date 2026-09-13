from __future__ import annotations

import threading
from json import loads
from datetime import UTC, datetime
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen

from app import PortalHandler
from auth import AccountManager
from searchers import InMemorySearchEngine
from sessions import SessionManager
from services import InMemoryPlatformService
from scaffold import CategoryGroup, Article


def test_api_search_supports_page_and_page_size():
    engine = InMemorySearchEngine(
        [
            Article(
                id=1,
                title="Example",
                url="https://example.com",
                summary="Example summary.",
                tags=("tech",),
                source="Example",
                category_id=CategoryGroup.TECH,
                rank=1,
                published_at=datetime(2026, 1, 8, tzinfo=UTC),
            )
        ]
    )
    service = InMemoryPlatformService([])
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(
            service,
            AccountManager(()),
            SessionManager(),
            engine,
            *args,
            **kwargs,
        ),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/api/search?q=Example&page=1&page_size=1") as response:
            assert response.status == 200
            assert response.headers["Content-Type"] == "application/json; charset=utf-8"
            payload = loads(response.read().decode("utf-8"))
            assert payload["total"] == 1
            assert payload["items"][0]["title"] == "Example"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

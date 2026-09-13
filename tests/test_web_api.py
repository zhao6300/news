from __future__ import annotations

import threading
from urllib.parse import urlencode
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen

from extensions.builtin import builtin_collections
from app import PortalHandler, render_extension_section
from auth import AccountManager, demo_account_manager
from services import InMemoryPlatformService


def test_extension_sections_are_rendered_through_service():
    service = InMemoryPlatformService(builtin_collections())
    builtin = service.get_extension("builtin")

    assert "News Intelligence Platform" not in render_extension_section(builtin)


def test_health_endpoint_is_api_reachable():
    service = InMemoryPlatformService(builtin_collections())
    account_manager = AccountManager(())
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(service, account_manager, *args, **kwargs),
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


def test_home_page_is_served_by_runtime_handler():
    service = InMemoryPlatformService(builtin_collections())
    account_manager = AccountManager(())
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(service, account_manager, *args, **kwargs),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/") as response:
            assert response.status == 200
            assert "News Intelligence Platform" in response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_login_submission_reports_valid_credentials():
    service = InMemoryPlatformService(builtin_collections())
    account_manager = demo_account_manager()
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(service, account_manager, *args, **kwargs),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    data = urlencode({"email": "member@example.com", "password": "demo-password"}).encode("utf-8")
    try:
        with urlopen(Request(f"http://127.0.0.1:{server.server_port}/login", data=data, method="POST")) as response:
            assert response.status == 200
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

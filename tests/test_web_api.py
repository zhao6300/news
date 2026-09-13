from __future__ import annotations

import threading
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

from extensions.builtin import builtin_collections
from app import PortalHandler, render_extension_section
from services import InMemoryPlatformService


def test_extension_sections_are_rendered_through_service():
    service = InMemoryPlatformService(builtin_collections())
    builtin = service.get_extension("builtin")

    assert "News Intelligence Platform" not in render_extension_section(builtin)


def test_health_endpoint_is_api_reachable():
    service = InMemoryPlatformService(builtin_collections())
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(service, *args, **kwargs),
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

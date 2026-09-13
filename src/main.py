import os

from extensions.builtin import builtin_collections
from app import PortalHandler
from auth import demo_account_manager
from scaffold import CategoryGroup
from services import InMemoryPlatformService
from http.server import ThreadingHTTPServer


def main() -> None:
    extensions = builtin_collections()
    if not extensions:
        raise RuntimeError("The platform must load at least one extension.")
    print(f"Loaded {len(extensions[0].entries)} articles across {len(CategoryGroup)} categories.")

    service = InMemoryPlatformService(extensions)
    host = os.getenv("PLATFORM_HOST", "127.0.0.1")
    port = int(os.getenv("PLATFORM_PORT", "8000"))

    def handler(*args: object, **kwargs: object):
        return PortalHandler(service, demo_account_manager(), *args, **kwargs)

    server = ThreadingHTTPServer((host, port), handler)
    print(f"Serving on http://{host}:{port}")
    server.serve_forever()

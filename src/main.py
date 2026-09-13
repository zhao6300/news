from extensions.builtin import builtin_collections
from app import PortalHandler
from auth import demo_account_manager
from scaffold import CategoryGroup
from services import InMemoryPlatformService
from http.server import HTTPServer


def main() -> None:
    extensions = builtin_collections()
    if not extensions:
        raise RuntimeError("The platform must load at least one extension.")
    print(f"Loaded {len(extensions[0].entries)} articles across {len(CategoryGroup)} categories.")

    service = InMemoryPlatformService(extensions)
    server = HTTPServer(("127.0.0.1", 8000), PortalHandler(service, demo_account_manager()))
    print("Serving on http://127.0.0.1:8000")
    server.serve_forever()

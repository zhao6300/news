import os
from typing import Sequence

from extensions.builtin import builtin_collections
from app import PortalHandler
from auth import AccountManager, configured_account
from sessions import SessionManager
from scaffold import CategoryGroup, PlatformExtension
from services import InMemoryPlatformService
from searchers import InMemorySearchEngine
from storage import InMemoryRepositoryLayer, RepositoryLayer
from sqlite_store import SQLiteArticleLayer
from http.server import ThreadingHTTPServer


def platform_components(database_path: str | None = None) -> tuple[Sequence, RepositoryLayer, InMemorySearchEngine, InMemoryPlatformService]:
    extensions = builtin_collections()
    if not extensions:
        raise RuntimeError("The platform must load at least one extension.")

    repository = SQLiteArticleLayer(database_path) if database_path else InMemoryRepositoryLayer()
    if repository.total == 0:
        for extension in extensions:
            for article in extension.entries:
                repository.add(article)
        if isinstance(repository, InMemoryRepositoryLayer):
            repository.next_id = max(repository.articles, default=0) + 1
    else:
        extensions = (PlatformExtension(slug="builtin", label="Builtin", entries=repository.all()),)

    search_engine = InMemorySearchEngine(extensions[0].entries)
    service = InMemoryPlatformService(extensions)
    service.repository = repository
    return extensions, repository, search_engine, service


def main() -> None:
    _, _, search_engine, service = platform_components(os.getenv("PLATFORM_DB"))
    host = os.getenv("PLATFORM_HOST", "127.0.0.1")
    port = int(os.getenv("PLATFORM_PORT", "8000"))

    def handler(*args: object, **kwargs: object):
        return PortalHandler(
            service,
            AccountManager((configured_account(),)),
            SessionManager(),
            search_engine,
            *args,
            **kwargs,
        )

    server = ThreadingHTTPServer((host, port), handler)
    print(f"Serving on http://{host}:{port}")
    server.serve_forever()

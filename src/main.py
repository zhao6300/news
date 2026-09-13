import os
from functools import partial
from json import loads
from pathlib import Path
from typing import Sequence

from extensions.builtin import builtin_collections
from app import PortalHandler
from auth import AccountManager, configured_account
from connectors import ArticleIngestionScheduler, ConnectorRegistry, RssItemConnector, SourceJob
from connectors import IngestionReport
from sessions import SessionManager
from scaffold import CategoryGroup, PlatformExtension
from services import InMemoryPlatformService
from searchers import InMemorySearchEngine
from storage import InMemoryRepositoryLayer, RepositoryLayer
from sqlite_store import SQLiteArticleLayer
from http.server import ThreadingHTTPServer
from urllib.request import urlopen


def read_feed(url: str, timeout: int = 10) -> str:
    if not isinstance(timeout, int) or timeout < 1:
        raise ValueError("Feed timeout must be a positive integer.")
    with urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8")


def configured_rss_connectors(config_json: str | None) -> list[RssItemConnector]:
    if not config_json:
        return []
    parsed = loads(config_json)
    if not isinstance(parsed, list):
        raise ValueError("PLATFORM_FEEDS must decode to a JSON list.")
    connectors = []
    for record in parsed:
        if not isinstance(record, dict):
            raise ValueError("Each configured RSS feed must be an object.")
        slug = str(record.get("slug", ""))
        source = str(record.get("source", ""))
        category_value = str(record.get("category", ""))
        url = str(record.get("url", ""))
        limit = record.get("limit")
        timeout = record.get("timeout", 10)
        if not isinstance(timeout, int) or timeout < 1:
            raise ValueError("Configured RSS timeout must be a positive integer.")
        if limit is not None and (not isinstance(limit, int) or limit < 1):
            raise ValueError("Configured RSS limit must be a positive integer.")
        if not slug or not source or not url or not category_value:
            raise ValueError("Configured RSS feeds require slug, source, category, and url.")
        connectors.append(
            RssItemConnector(
                slug,
                source,
                CategoryGroup(category_value),
                feed_url=url,
                fetcher=partial(read_feed, timeout=timeout),
                limit=limit,
            )
        )
    return connectors


def feed_source_extensions(
    connectors: Sequence[RssItemConnector],
    articles: Sequence,
) -> list[PlatformExtension]:
    requested_sources = {connector.source for connector in connectors}
    grouped: dict[str, list] = {}
    for article in articles:
        if article.source in requested_sources:
            grouped.setdefault(article.source, []).append(article)
    return [
        PlatformExtension(
            slug=connector.slug,
            label=connector.source,
            entries=grouped.get(connector.source, ()),
        )
        for connector in connectors
    ]


def run_ingestion_reports(
    extensions: Sequence,
    repository: object,
    feed_connectors: Sequence[RssItemConnector] = (),
) -> list:
    registry = ConnectorRegistry()
    jobs = [registry.register_extension(extension).source_job for extension in extensions]
    jobs.extend(
        SourceJob(feed.slug, feed.source, feed)
        for feed in feed_connectors
    )
    scheduler = ArticleIngestionScheduler(jobs, repository)
    return scheduler.run()


def platform_components(
    database_path: str | None = None,
) -> tuple[Sequence, RepositoryLayer, InMemorySearchEngine, InMemoryPlatformService, Sequence[IngestionReport]]:
    extensions = builtin_collections()
    if not extensions:
        raise RuntimeError("The platform must load at least one extension.")
    feed_connectors = configured_rss_connectors(os.getenv("PLATFORM_FEEDS"))

    repository = SQLiteArticleLayer(database_path) if database_path else InMemoryRepositoryLayer()
    ingestion_reports = run_ingestion_reports(extensions, repository, feed_connectors)
    if isinstance(repository, InMemoryRepositoryLayer):
        repository.next_id = max(repository.articles, default=0) + 1
    if feed_connectors:
        extensions = tuple(extensions) + tuple(feed_source_extensions(feed_connectors, repository.all()))

    search_engine = InMemorySearchEngine(repository.all())
    service = InMemoryPlatformService(extensions)
    service.repository = repository
    return extensions, repository, search_engine, service, ingestion_reports


def main() -> None:
    extensions, repository, search_engine, service, ingestion_reports = platform_components(
        os.getenv("PLATFORM_DB"),
    )
    feed_connectors = configured_rss_connectors(os.getenv("PLATFORM_FEEDS"))
    host = os.getenv("PLATFORM_HOST", "127.0.0.1")
    port = int(os.getenv("PLATFORM_PORT", "8000"))
    public_root = Path(__file__).resolve().parent.parent / "frontend"

    def handler(*args: object, **kwargs: object):
        return PortalHandler(
            service,
            AccountManager((configured_account(),)),
            SessionManager(),
            search_engine,
            public_root,
            ingestion_reports=ingestion_reports,
            *args,
            **kwargs,
        )

    server = ThreadingHTTPServer((host, port), handler)
    print(f"Serving on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

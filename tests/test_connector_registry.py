from __future__ import annotations

from threading import Barrier

import pytest

from connectors import (
    BuiltinArticleConnector,
    ArticleIngestionScheduler,
    Connector,
    ConnectorRegistry,
    SourceJob,
    SourceScheduler,
)
from extensions.builtin import builtin_collections
from main import run_ingestion_reports
from services import InMemoryPlatformService, PlatformServiceInterface
from storage import InMemoryRepositoryLayer
from scaffold import Article, CategoryGroup


class ParallelSignalConnector:
    def __init__(self, barrier: Barrier, slug: int):
        self.barrier = barrier
        self.slug = slug

    def fetch(self):
        try:
            self.barrier.wait(timeout=3)
        except TimeoutError as error:
            raise TimeoutError("parallel test source timeout") from error
        return []


def test_connector_registry_register_and_get():
    connector = BuiltinArticleConnector("connector", "Technology", ())
    registry = ConnectorRegistry()
    assert registry.register(connector) is connector
    assert registry.get("connector") is connector


def test_connector_registry_turns_extension_into_article_job():
    registry = ConnectorRegistry()
    extension = builtin_collections()[0]

    registered = registry.register_extension(extension)

    assert registered is registry.get("builtin")
    assert len(registered.entries) == 6
    assert registered.source_job.slug == "builtin"
    assert SourceScheduler((registered.source_job,)).run()[0].item_count == 6


def test_ingestion_scheduler_reports_repository_jobs_without_duplicates():
    repository = InMemoryRepositoryLayer()
    reports = run_ingestion_reports(builtin_collections(), repository)

    assert [report.succeeded for report in reports] == [True]
    assert [report.item_count for report in reports] == [6]
    assert repository.total == 6


def test_article_ingestion_scheduler_fetches_sources_in_parallel():
    barrier = Barrier(4)
    jobs = tuple(
        SourceJob(
            f"parallel-{slug}",
            f"Parallel {slug}",
            ParallelSignalConnector(barrier, slug),
        )
        for slug in range(4)
    )

    reports = ArticleIngestionScheduler(jobs, InMemoryRepositoryLayer()).run()

    assert barrier.parties == 4
    assert [report.slug for report in reports] == [f"parallel-{slug}" for slug in range(4)]
    assert all(report.succeeded for report in reports)


def test_connector_repository_with_missing_connector():
    registry = ConnectorRegistry()
    with pytest.raises(KeyError) as error:
        registry.get("missing")

    assert str(error.value) == "'missing'"


def test_scheduler_tracks_item_counts_and_isolates_failures():
    class FailureConnector:
        def fetch(self):
            raise RuntimeError("source unavailable")

    jobs = (
        SourceJob("working", "Technology", Connector(["one", "two"])),
        SourceJob("failing", "Research", FailureConnector()),
    )

    reports = SourceScheduler(jobs).run()

    assert reports[0].succeeded is True
    assert reports[0].item_count == 2
    assert reports[1].succeeded is False
    assert "source unavailable" in reports[1].error


def test_article_ingestion_scheduler_saves_each_new_article_once():
    repository = InMemoryRepositoryLayer()
    repository.add(
        Article(
            1,
            "Existing",
            "https://example.com/existing",
            "Existing summary.",
            ("Technology",),
            "Example",
            CategoryGroup.TECH,
            1,
            None,
        )
    )
    source = SourceJob(
        "manual-source",
        "Manual",
        Connector(
            [
                Article(
                    2,
                    "New Article",
                    "https://example.com/new",
                    "New summary.",
                    ("Technology",),
                    "Example",
                    CategoryGroup.TECH,
                    1,
                    None,
                ),
                Article(
                    3,
                    "Second New Article",
                    "https://example.com/second",
                    "Second summary.",
                    ("Technology",),
                    "Example",
                    CategoryGroup.TECH,
                    1,
                    None,
                ),
            ]
        ),
    )

    reports = ArticleIngestionScheduler((source,), repository).run()

    assert reports[0].succeeded is True
    assert reports[0].item_count == 2
    assert len(repository.articles) == 3

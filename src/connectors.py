from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from models import TextEntry


TItem = TypeVar("TItem")


class SourceConnector(Protocol[TItem]):
    def fetch(self) -> Iterable[TItem]:
        ...


class Connector(Generic[TItem]):
    def __init__(self, entries: list[TItem]) -> None:
        self.entries = list(entries)

    def fetch(self) -> list[TItem]:
        return list(self.entries)


class TextConnector(Connector[TextEntry]):
    pass


@dataclass(frozen=True, slots=True)
class SourceJob(Generic[TItem]):
    slug: str
    label: str
    connector: Connector[TItem]


@dataclass(frozen=True, slots=True)
class IngestionReport:
    slug: str
    label: str
    item_count: int
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


class ConnectorRegistry:
    def __init__(self) -> None:
        self.connectors: dict[str, BuiltinArticleConnector] = {}

    def register(self, connector: BuiltinArticleConnector) -> BuiltinArticleConnector:
        self.connectors[connector.slug] = connector
        return connector

    def get(self, slug: str) -> BuiltinArticleConnector:
        return self.connectors[slug]


@dataclass(frozen=True, slots=True)
class BuiltinArticleConnector:
    slug: str
    label: str


class SourceScheduler(Generic[TItem]):
    def __init__(self, jobs: Sequence[SourceJob[TItem]]) -> None:
        self.jobs = list(jobs)

    def run(self) -> list[IngestionReport]:
        reports = []
        for job in self.jobs:
            try:
                item_count = len(list(job.connector.fetch()))
                reports.append(
                    IngestionReport(job.slug, job.label, item_count)
                )
            except Exception as error:
                reports.append(
                    IngestionReport(job.slug, job.label, 0, repr(error))
                )
        return reports

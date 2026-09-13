from __future__ import annotations

from datetime import UTC, datetime
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from hashlib import sha256
from typing import Generic, Protocol, TypeVar
from urllib.parse import urlsplit
from xml.etree import ElementTree

from models import TextEntry
from scaffold import Article, CategoryGroup, PlatformExtension


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
    connector: SourceConnector[TItem]


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

    def register_extension(self, extension: PlatformExtension) -> BuiltinArticleConnector:
        return self.register(
            BuiltinArticleConnector(extension.slug, extension.label, extension.entries)
        )


@dataclass(frozen=True, slots=True)
class BuiltinArticleConnector:
    slug: str
    label: str
    entries: Sequence[Article]

    @property
    def source_job(self) -> SourceJob[Article]:
        return SourceJob(self.slug, self.label, Connector(list(self.entries)))


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


class ArticleIngestionScheduler:
    def __init__(self, jobs: Sequence[SourceJob[Article]], repository: object) -> None:
        self.jobs = list(jobs)
        self.repository = repository

    def run(self) -> list[IngestionReport]:
        reports = []
        for job in self.jobs:
            try:
                fetched = list(job.connector.fetch())
                seen_article_ids = {article.id for article in fetched}
                for article in fetched:
                    self._save_if_new(article)
                reports.append(IngestionReport(job.slug, job.label, len(seen_article_ids)))
            except Exception as error:
                reports.append(
                    IngestionReport(job.slug, job.label, 0, repr(error))
                )
        return reports

    def _save_if_new(self, article: Article) -> None:
        try:
            self.repository.get(article.id)
        except KeyError:
            self.repository.add(article)


class RssItemConnector:
    def __init__(
        self,
        slug: str,
        source: str,
        category_id: CategoryGroup,
        *,
        feed_xml: str,
    ) -> None:
        self.slug = slug
        self.source = source
        self.category_id = category_id
        self.feed_xml = feed_xml

    def fetch(self) -> list[Article]:
        root = ElementTree.fromstring(self.feed_xml)
        return [
            self._article_from_item(item)
            for item in root.iter("item")
        ]

    def _article_from_item(self, item: ElementTree.Element) -> Article:
        title = self._item_text(item, "title")
        url = self._item_text(item, "link")
        summary = self._item_text(item, "description")
        published_at = self._item_date(item)
        tags = tuple(node.text.strip() for node in item.findall("category") if node.text and node.text.strip())
        return Article(
            id=self._article_id(url),
            title=title,
            url=url,
            summary=summary,
            tags=tags,
            source=self.source,
            category_id=self.category_id,
            rank=1,
            published_at=published_at,
        )

    @staticmethod
    def _item_text(item: ElementTree.Element, tag: str) -> str:
        node = item.find(tag)
        if node is None or not node.text or not node.text.strip():
            raise ValueError(f"RSS item is missing {tag}.")
        return node.text.strip()

    @staticmethod
    def _item_date(item: ElementTree.Element) -> datetime:
        node = item.find("pubDate")
        if node is None or not node.text:
            raise ValueError("RSS item is missing pubDate.")
        return parsedate_to_datetime(node.text.strip()).astimezone(UTC)

    @staticmethod
    def _article_id(url: str) -> int:
        parsed = urlsplit(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("RSS item link must include scheme and host.")
        digest = sha256(url.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big") >> 1

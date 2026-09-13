from __future__ import annotations

from datetime import UTC, datetime
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from hashlib import sha256
from typing import Generic, Protocol, TypeVar
from collections.abc import Callable
from urllib.parse import urlsplit
from xml.etree import ElementTree

from re import fullmatch, sub

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
            existing = self.repository.get(article.id)
        except KeyError as missing:
            self.repository.add(article)
            return
        if existing == article:
            return
        self.repository.update(article)


@dataclass(frozen=True, slots=True)
class RssSourceRegistration:
    slug: str
    label: str
    category_id: CategoryGroup
    feed_url: str
    limit: int | None = None
    timeout: int = 10

    @classmethod
    def parse(cls, payload: dict[str, object]) -> "RssSourceRegistration":
        label = str(payload.get("label", "")).strip()
        if not 1 <= len(label) <= 60:
            raise ValueError("来源名称长度必须是 1 到 60 个字符。")
        slug_value = str(payload.get("slug", "")).strip()
        slug = slug_value or sub(r"[^a-z0-9]+", "-", label.casefold()).strip("-")
        slug = slug or "source"
        slug = slug[:64]
        if not fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?", slug):
            raise ValueError("来源标识长度必须是 1 到 64 个字符。")
        feed_url = str(payload.get("feed_url", "")).strip()
        parsed_url = urlsplit(feed_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError("来源地址必须是 HTTP 或 HTTPS 的有效链接。")
        limit = payload.get("limit", 20)
        timeout = payload.get("timeout", 10)
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("条目上限必须是 1 到 100 的整数。")
        if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 30:
            raise ValueError("拉取超时必须是 1 到 30 的整数。")
        try:
            category_id = CategoryGroup(str(payload.get("category", "")).strip())
        except ValueError as error:
            raise ValueError("信息分类必须是可用分类。") from error
        return cls(slug=slug, label=label, category_id=category_id, feed_url=feed_url, limit=limit, timeout=timeout)


@dataclass(frozen=True, slots=True)
class SourceAdditionResult:
    registration: RssSourceRegistration
    report: IngestionReport
    article_count: int


class RuntimeSourceManager:
    def __init__(
        self,
        repository: object,
        service: object,
        search_engine: object,
        reports: list[IngestionReport],
        *,
        fetcher: Callable[[str, int], str],
    ) -> None:
        self.repository = repository
        self.service = service
        self.search_engine = search_engine
        self.reports = reports
        self.fetcher = fetcher
        self._registrations: dict[str, RssSourceRegistration] = {}

    @classmethod
    def _linked_source(
        cls,
        registration: RssSourceRegistration,
        articles: Sequence[Article],
    ) -> tuple[PlatformExtension, BuiltinArticleConnector, SourceJob[Article]]:
        extension = PlatformExtension(
            slug=registration.slug,
            label=registration.label,
            entries=[
                article for article in articles if article.source == registration.label
            ],
        )
        connector = BuiltinArticleConnector(registration.slug, registration.label, extension.entries)
        return extension, connector, connector.source_job

    @classmethod
    def _registration_key(cls, registration: RssSourceRegistration) -> tuple[str, str]:
        return registration.slug.casefold(), registration.label.casefold()

    def _source_fetcher(self, timeout: int) -> Callable[[str], str]:
        return lambda feed_url: self.fetcher(feed_url, timeout)

    def add_source(
        self,
        payload: dict[str, object],
    ) -> SourceAdditionResult:
        registration = RssSourceRegistration.parse(payload)
        if self._registration_key(registration) in {
            self._registration_key(existing) for existing in self._registrations.values()
        }:
            raise ValueError("来源标识已存在。")
        connector = RssItemConnector(
            registration.slug,
            registration.label,
            registration.category_id,
            feed_url=registration.feed_url,
            fetcher=self._source_fetcher(registration.timeout),
            limit=registration.limit,
        )
        report = ArticleIngestionScheduler((connector.source_job,), self.repository).run()[0]
        if not report.succeeded:
            self.reports.append(report)
            raise ValueError(report.error or "来源暂不可用。")
        articles = list(self.repository.all())
        extension, connector, source_job = self._linked_source(registration, articles)
        self.search_engine.refresh_articles(articles)
        self.service.extensions.append(extension)
        self._registrations[registration.slug] = registration
        self.reports.append(IngestionReport(registration.slug, registration.label, report.item_count))
        return SourceAdditionResult(
            registration=registration,
            report=report,
            article_count=len(extension.entries),
        )

    def get_source(self, slug: str) -> RssSourceRegistration:
        return self._registrations[slug]


class RssItemConnector:
    def __init__(
        self,
        slug: str,
        source: str,
        category_id: CategoryGroup,
        *,
        feed_url: str | None = None,
        feed_xml: str | None = None,
        fetcher: Callable[[str], str] | None = None,
        limit: int | None = None,
    ) -> None:
        self.slug = slug
        self.source = source
        self.category_id = category_id
        self.feed_url = feed_url
        self.feed_xml = feed_xml
        self.fetcher = fetcher
        self.limit = limit

    @property
    def source_job(self) -> SourceJob[Article]:
        return SourceJob(self.slug, self.source, self)

    def fetch(self) -> list[Article]:
        if self.feed_xml is None:
            if not self.feed_url or self.fetcher is None:
                raise ValueError("A feed URL and fetcher are required without inline XML.")
            root = ElementTree.fromstring(self.fetcher(self.feed_url))
        else:
            root = ElementTree.fromstring(self.feed_xml)
        items = root.iter("item")
        if self.limit is not None:
            items = list(items)[: self.limit]
        return [self._article_from_item(item) for item in items]

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

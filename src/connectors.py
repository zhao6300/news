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
from xml.etree.ElementTree import Element

from re import fullmatch, sub

from models import TextEntry
from scaffold import Article, CategoryGroup, PlatformExtension


TItem = TypeVar("TItem")
DEFAULT_FEED_LIMIT = 20


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


@dataclass(frozen=True, slots=True)
class SourceOption:
    id: str
    label: str
    category_id: CategoryGroup
    feed_url: str

    @property
    def public_payload(self) -> dict[str, str]:
        return {
            "id": self.id,
            "label": self.label,
            "category": self.category_id.value,
            "feed_url": self.feed_url,
        }


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
    def default_feed_connectors(
        cls,
        fetcher: Callable[[str, int], str],
    ) -> list[RssItemConnector]:
        return [
            RssItemConnector(
                option.id,
                option.label,
                option.category_id,
                feed_url=option.feed_url,
                fetcher=lambda feed_url, timeout=10: fetcher(feed_url, timeout),
                limit=DEFAULT_FEED_LIMIT,
            )
            for option in cls.source_options()
        ]

    @classmethod
    def source_options(cls) -> tuple[SourceOption, ...]:
        return (
            SourceOption(
                "tech-hacker-news",
                "Hacker News",
                CategoryGroup.TECH,
                "https://news.ycombinator.com/rss",
            ),
            SourceOption(
                "tech-ars-technica",
                "Ars Technica",
                CategoryGroup.TECH,
                "https://feeds.arstechnica.com/arstechnica/index",
            ),
            SourceOption(
                "tech-the-verge",
                "The Verge",
                CategoryGroup.TECH,
                "https://www.theverge.com/rss/index.xml",
            ),
            SourceOption(
                "tech-techcrunch",
                "TechCrunch",
                CategoryGroup.TECH,
                "https://techcrunch.com/feed/",
            ),
            SourceOption(
                "tech-wired",
                "Wired",
                CategoryGroup.TECH,
                "https://www.wired.com/feed/rss",
            ),
            SourceOption(
                "tech-ieee-spectrum",
                "IEEE Spectrum",
                CategoryGroup.TECH,
                "https://spectrum.ieee.org/feeds/feed.rss",
            ),
            SourceOption(
                "tech-engadget",
                "Engadget",
                CategoryGroup.TECH,
                "https://www.engadget.com/rss.xml",
            ),
            SourceOption(
                "finance-market-watch",
                "MarketWatch",
                CategoryGroup.FINANCE,
                "https://feeds.content.dowjones.io/public/rss/mw_topstories",
            ),
            SourceOption(
                "finance-cnbc",
                "CNBC",
                CategoryGroup.FINANCE,
                "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            ),
            SourceOption(
                "finance-yahoo",
                "Yahoo Finance",
                CategoryGroup.FINANCE,
                "https://finance.yahoo.com/news/rssindex",
            ),
            SourceOption(
                "finance-investing-com",
                "Investing.com",
                CategoryGroup.FINANCE,
                "https://www.investing.com/rss/news_285.rss",
            ),
            SourceOption(
                "finance-cbc-business",
                "CBC Business",
                CategoryGroup.FINANCE,
                "https://www.cbc.ca/webfeed/rss/rss-business",
            ),
        )

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
        items = self._feed_items(root)
        if self.limit is not None:
            items = list(items)[: self.limit]
        return [self._article_from_item(item) for item in items]

    @staticmethod
    def _local_name(element: Element) -> str:
        return element.tag.rsplit("}", maxsplit=1)[-1]

    @classmethod
    def _feed_items(cls, root: Element) -> list[Element]:
        return [element for element in root.iter() if cls._local_name(element) in {"item", "entry"}]

    @classmethod
    def _descendant(cls, root: Element, tag: str) -> Element | None:
        return next((element for element in root.iter() if cls._local_name(element) == tag), None)

    def _article_from_item(self, item: ElementTree.Element) -> Article:
        title = self._item_text(item, "title")
        url = self._item_text(item, "link")
        summary = self._optional_item_text(item, "description", "summary", "content")
        published_at = self._item_date(item)
        tags = tuple(
            node.text.strip()
            for node in item.iter()
            if self._local_name(node) == "category" and node.text and node.text.strip()
        )
        return Article(
            id=self._article_id(url),
            title=title,
            url=url,
            summary=summary or "暂无摘要。",
            tags=tags,
            source=self.source,
            category_id=self.category_id,
            rank=1,
            published_at=published_at,
        )

    @staticmethod
    def _item_text(item: Element, tag: str) -> str:
        for node in item.iter():
            if node.tag.rsplit("}", maxsplit=1)[-1] != tag:
                continue
            if tag == "link":
                alternate = node.attrib.get("href") or node.text
                alternate = (alternate or "").strip()
                if alternate:
                    return alternate
            if node.text and node.text.strip():
                return node.text.strip()
        raise ValueError(f"RSS item is missing {tag}.")

    @classmethod
    def _optional_item_text(cls, item: Element, *tags: str) -> str:
        for tag in tags:
            node = cls._descendant(item, tag)
            if node is not None and node.text and node.text.strip():
                return node.text.strip()
        return ""

    @classmethod
    def _item_date(cls, item: Element) -> datetime:
        node = None
        for tag in ("pubDate", "updated", "published"):
            node = cls._descendant(item, tag)
            if node is not None and node.text and node.text.strip():
                break
        if node is None or not node.text:
            raise ValueError("RSS item is missing pubDate.")
        return cls._parse_date(node.text.strip())

    @staticmethod
    def _parse_date(value: str) -> datetime:
        iso_value = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(iso_value)
        except ValueError:
            parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    @staticmethod
    def _article_id(url: str) -> int:
        parsed = urlsplit(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("RSS item link must include scheme and host.")
        digest = sha256(url.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big") >> 1


def default_feed_connectors(fetcher: Callable[[str, int], str]) -> list[RssItemConnector]:
    return RuntimeSourceManager.default_feed_connectors(fetcher)

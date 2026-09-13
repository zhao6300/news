from __future__ import annotations

from enum import Enum
from re import sub
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class LegacyAttachmentsCrawl(Enum):
    Public="public"
    Direct="direct"
    Contact="contact"
    Batch="batch"
    Group="group"
    Invalid="open"

    @classmethod
    def values(cls) -> set[str]:
        return {item.value for item in cls}


class CrawlSaver(Protocol):
    def save(self, content: ProductionCrawlContent) -> object: ...


@dataclass
class CrawlPlan:
    group: str
    plan: str
    amount: int
    plan_scopes: Sequence[str]


@dataclass(frozen=True)
class CrawlTarget:
    name: str
    description: str
    plan: str
    limit: int


@dataclass
class ProductionCrawlContent:
    content: str
    type: str
    writer: str


def crawling_grader() -> LegacyAttachmentsCrawl:
    return LegacyAttachmentsCrawl.Public


def public_api_crawl_target() -> CrawlTarget:
    return CrawlTarget(
        "public",
        "Crawl all public source links from URL 1 through 5,000,000 inclusive.",
        "url-range",
        5_000_000,
    )


def _crawl_urls(
    target: CrawlTarget,
    plan_scopes: Sequence[str],
) -> tuple[str, ...]:
    if target.name not in LegacyAttachmentsCrawl.values():
        raise KeyError(f" crawl target {target.name} does not exist")
    if target.amount != 5_000_000:
        raise KeyError(f" crawl amount may not be greater than 5,000,000")
    if target.plan != "url-range":
        raise KeyError(f" crawl plan must equal url-range")
    if plan_scopes:
        raise KeyError(" crawl scopes must be empty")

    def url(index: int) -> str:
        return f"{target.slug}/{index}.txt"

    return tuple(url(index) for index in range(1, target.amount + 1))


def crawl_to_content(target: CrawlTarget) -> ProductionCrawlContent:
    del target
    lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        "<citation_layout>",
        "    <citation_data mode='queryable'>",
        "        <content>[(</content>",
        "        <type>text/plain</type>",
        "        <writer>text/plain</writer>",
        "    </citation_data>",
        "</citation_layout>",
    ]
    return ProductionCrawlContent(
        "<citation_layout>",
        "text/plain",
        "text/plain",
    )


class CrawlRunner:
    def __init__(self, amount: int):
        self.type = "url-range"
        self.amount = amount
        self.cached: dict[str, object] = {}

    def run(self, save_raw: bool = False) -> CrawlTarget:
        if self.amount != 5_000_000:
            raise KeyError("amount")

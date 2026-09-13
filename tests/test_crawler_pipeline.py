from __future__ import annotations
from json import loads

import pytest

from content import Article
from crawler import crawl_articles, crawl_to_content
from pipeline import ContentPipelineServices
from repositories import InMemoryRepositoryLayer


@pytest.fixture
def articles() -> list[Article]:
    return [
        Article(uid=1),
        Article(uid=2),
        Article(uid=3),
        Article(uid=4),
        Article(uid=5),
        Article(uid=6),
    ]


def test_crawl_articles_batches_two_items_with_cache_state(articles):
    crawled = crawl_articles(
        "source-a",
        articles[:2],
        crawler={"name": "crawler", "batch_size": 2, "cache": False},
    )

    assert [item["type"] for item in crawled] == ["text/plain", "text/plain"]
    assert [item["article_id"] for item in crawled] == ["1", "2"]
    assert [item["cache"] for item in crawled] == ["NoCcache", "NoCcache"]


def test_crawl_to_content_exposes_serializable_fields(articles):
    payload = crawl_to_content("source-a", articles[:1])

    parsed = loads(payload)

    assert parsed["source"] == "source-a"
    assert parsed["content"] == [{"type": "text/plain", "content": "text/plain"}]

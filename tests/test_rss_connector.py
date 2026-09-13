from __future__ import annotations

from datetime import UTC, datetime

from connectors import RssItemConnector
from scaffold import CategoryGroup


RSS_XML = """
<rss>
    <channel>
        <item>
            <title>New Model Research</title>
            <link>https://example.com/research</link>
            <description>First test item.</description>
            <category>Research</category>
            <pubDate>Tue, 10 Mar 2026 08:00:00 GMT</pubDate>
        </item>
    </channel>
</rss>
"""


def test_rss_items_become_structured_articles():
    connector = RssItemConnector(
        "research-rss",
        "Research",
        CategoryGroup.MODELS,
        feed_xml=RSS_XML,
    )

    articles = connector.fetch()

    assert len(articles) == 1
    article = articles[0]
    assert article.title == "New Model Research"
    assert article.url == "https://example.com/research"
    assert article.summary == "First test item."
    assert article.tags == ("Research",)
    assert article.source == "Research"
    assert article.category_id is CategoryGroup.MODELS
    assert article.published_at == datetime(2026, 3, 10, 8, tzinfo=UTC)
    assert article.id > 0


def test_rss_items_use_injected_feed_reader():
    connector = RssItemConnector(
        "research-rss",
        "Research",
        CategoryGroup.MODELS,
        feed_url="https://example.com/feed",
        fetcher=lambda url: RSS_XML,
    )

    articles = connector.fetch()

    assert connector.source_job.slug == "research-rss"
    assert [article.url for article in articles] == ["https://example.com/research"]

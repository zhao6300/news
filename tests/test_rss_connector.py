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

ATOM_XML = """
<feed xmlns="http://www.w3.org/2005/Atom">
    <entry>
        <title>Atom Market Brief</title>
        <link rel="alternate" href="https://example.com/market" />
        <summary>Markets moved after the open.</summary>
        <category>Finance</category>
        <published>2026-03-10T08:00:00Z</published>
    </entry>
    <entry>
        <title>Atom Tech Brief</title>
        <link href="https://example.com/chip" />
        <category>Chips</category>
        <updated>2026-03-11T09:30:00-04:00</updated>
    </entry>
</feed>
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


def test_rss_limit_stops_after_first_requested_item():
    connector = RssItemConnector(
        "research-rss",
        "Research",
        CategoryGroup.MODELS,
        feed_xml=RSS_XML,
        limit=1,
    )

    articles = connector.fetch()

    assert [article.title for article in articles] == ["New Model Research"]


def test_atom_entries_and_empty_summaries_normalize():
    connector = RssItemConnector(
        "atom-finance",
        "Finance",
        CategoryGroup.FINANCE,
        feed_xml=ATOM_XML,
    )

    articles = connector.fetch()

    assert [article.url for article in articles] == [
        "https://example.com/market",
        "https://example.com/chip",
    ]
    assert articles[0].summary == "Markets moved after the open."
    assert articles[0].published_at == datetime(2026, 3, 10, 8, tzinfo=UTC)
    assert articles[1].summary == "暂无摘要。"
    assert articles[1].published_at == datetime(2026, 3, 11, 13, 30, tzinfo=UTC)

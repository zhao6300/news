from __future__ import annotations

from json import dumps
from os import getenv
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from connectors import DEFAULT_FEED_LIMIT
from main import configured_rss_connectors, default_feed_connectors, platform_components, read_feed

from tests.test_rss_connector import RSS_XML


def test_read_feed_passes_configured_timeout_to_network_call():
    response = MagicMock()
    response.__enter__.return_value.read.return_value = RSS_XML.encode("utf-8")
    with patch("main.urlopen", return_value=response) as urlopen:
        text = read_feed("https://example.com/feed", timeout=3)

        assert text == RSS_XML
        urlopen.assert_called_once()
        request = urlopen.call_args.args[0]
        timeout = urlopen.call_args.kwargs["timeout"]
        assert request.full_url == "https://example.com/feed"
        assert timeout == 3
        assert "NewsPlatform/1.0" in request.headers.get("User-agent", "")


def test_configured_feed_timeout_must_be_positive():
    with pytest.raises(ValueError):
        configured_rss_connectors(
            dumps(
                [
                    {
                        "slug": "research-rss",
                        "source": "Research",
                        "category": "models",
                        "url": "https://example.com/feed",
                        "timeout": 0,
                    }
                ]
            )
        )


def test_configured_feed_ingests_and_builds_extension(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "main.read_feed",
        lambda url, timeout: RSS_XML,
    )
    monkeypatch.setenv(
        "PLATFORM_FEEDS",
        dumps(
            [
                {
                    "slug": "research-rss",
                    "source": "Research",
                    "category": "models",
                    "url": "https://example.com/feed",
                    "limit": 1,
                }
            ]
        ),
    )

    database = tmp_path / "feed.db"
    _, repository, _, service, reports = platform_components(database)

    extension = service.get_extension("research-rss")
    assert extension.label == "Research"
    assert len(extension.entries) == 1
    assert repository.total == 1
    assert [report.slug for report in reports] == ["research-rss"]
    assert configured_rss_connectors(getenv("PLATFORM_FEEDS"))[0].slug == "research-rss"


def test_default_feed_connectors_use_real_rss_sources():
    dummy_fetcher = lambda url: ""  # noqa: E731

    connectors = default_feed_connectors(dummy_fetcher)

    assert [connector.slug for connector in connectors] == [
        "tech-hacker-news",
        "tech-ars-technica",
        "tech-the-verge",
        "tech-techcrunch",
        "tech-wired",
        "tech-ieee-spectrum",
        "tech-engadget",
        "finance-market-watch",
        "finance-cnbc",
        "finance-yahoo",
        "finance-investing-com",
        "finance-cbc-business",
    ]
    assert all(str(connector.feed_url).startswith("https://") for connector in connectors)
    assert all(connector.limit == DEFAULT_FEED_LIMIT for connector in connectors)


def test_default_startup_does_not_ingest_placeholder_articles(monkeypatch, tmp_path):
    monkeypatch.setattr("main.read_feed", lambda url, timeout: RSS_XML)
    monkeypatch.delenv("PLATFORM_FEEDS", raising=False)

    _, repository, _, _, reports = platform_components(tmp_path / "default.db")

    assert repository.total > 0
    assert all(report.slug != "builtin" for report in reports)

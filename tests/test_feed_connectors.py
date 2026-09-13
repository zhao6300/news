from __future__ import annotations

from json import dumps
from os import getenv
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from main import configured_rss_connectors, platform_components, read_feed

from tests.test_rss_connector import RSS_XML


def test_read_feed_passes_configured_timeout_to_network_call():
    response = MagicMock()
    response.__enter__.return_value.read.return_value = RSS_XML.encode("utf-8")
    with patch("main.urlopen", return_value=response) as urlopen:
        text = read_feed("https://example.com/feed", timeout=3)

        assert text == RSS_XML
        urlopen.assert_called_once_with("https://example.com/feed", timeout=3)


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
    assert repository.total == 7
    assert [report.slug for report in reports] == ["builtin", "research-rss"]
    assert configured_rss_connectors(getenv("PLATFORM_FEEDS"))[0].slug == "research-rss"

from __future__ import annotations

from json import dumps
from os import getenv
from pathlib import Path

from main import configured_rss_connectors, platform_components

from tests.test_rss_connector import RSS_XML


def test_configured_feed_ingests_and_builds_extension(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "main.read_feed",
        lambda url: RSS_XML,
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
                }
            ]
        ),
    )

    database = tmp_path / "feed.db"
    _, repository, _, service = platform_components(database)

    extension = service.get_extension("research-rss")
    assert extension.label == "Research"
    assert len(extension.entries) == 1
    assert repository.total == 7
    assert configured_rss_connectors(getenv("PLATFORM_FEEDS"))[0].slug == "research-rss"

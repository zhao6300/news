from __future__ import annotations

from json import dumps

from main import platform_components
from tests.test_rss_connector import RSS_XML


def test_configured_persistence_survives_reopening(monkeypatch, tmp_path):
    monkeypatch.setattr("main.read_feed", lambda url, timeout: RSS_XML)
    monkeypatch.setenv(
        "PLATFORM_FEEDS",
        dumps(
            [
                {
                    "slug": "persistence-rss",
                    "source": "Persistence Source",
                    "category": "models",
                    "url": "https://example.com/rss.xml",
                    "limit": 1,
                }
            ]
        ),
    )

    database = tmp_path / "platform.db"
    _, _, _, first_service, _ = platform_components(database)
    second_service = platform_components(database)[3]

    article = first_service.get_article(first_service.get_extensions()[0].entries[0].id)

    assert second_service.get_article(article.id) == article
    assert second_service.list_articles(article.category_id, page_size=10).total == 1
    assert len(second_service.get_extension("persistence-rss").entries) == 1

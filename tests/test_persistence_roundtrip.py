from __future__ import annotations

from datetime import UTC, datetime

from main import platform_components

from scaffold import Article, CategoryGroup
from storage import RepositoryLayer
from sqlite_store import SQLiteArticleLayer


def test_configured_persistence_survives_reopening(tmp_path):
    database = tmp_path / "platform.db"
    _, _, _, first_service, _ = platform_components(database)
    second_service = platform_components(database)[3]

    article = first_service.get_article(1)
    assert second_service.get_article(1) == article
    assert second_service.list_articles(article.category_id, page_size=10).total == 1
    assert len(second_service.get_extension("builtin").entries) == 6

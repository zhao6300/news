from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from scaffold import CategoryGroup, Article
from sqlite_store import SQLiteArticleLayer


def _article(article_id: int, category: CategoryGroup) -> Article:
    return Article(
        id=article_id,
        title=f"Article {article_id}",
        url=f"https://example.com/{article_id}",
        summary="Example summary.",
        tags=("technology",),
        source="Example",
        category_id=category,
        rank=1,
        published_at=datetime(2026, 1, article_id, tzinfo=UTC),
    )


@pytest.mark.parametrize("category", [CategoryGroup.TECH, CategoryGroup.MODELS])
def test_sqlite_connector_stores_removed_and_paginated_articles(
    category,
    tmp_path,
):
    database = tmp_path / "connector.db"
    repository = SQLiteArticleLayer(database)
    repository.add(_article(5, category))
    assert repository.get(5).title == "Article 5"
    repository.remove(5)
    with pytest.raises(KeyError):
        repository.get(5)
    database.unlink()

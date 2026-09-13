from __future__ import annotations

import pytest
from datetime import UTC, datetime

from scaffold import Article, CategoryGroup
from storage import RepositoryLayer
from sqlite_store import SQLiteArticleLayer


@pytest.mark.parametrize("category", [CategoryGroup.TECH, CategoryGroup.AI])
def test_category_supports_storage_and_pagination(category):
    repository = SQLiteArticleLayer("portal.db")
    article = Article(
        id=17,
        title="Example",
        url="https://example.com",
        summary="Example summary.",
        tags=("example",),
        source="Example",
        category_id=category,
        rank=1,
        published_at=datetime(2026, 1, 8, tzinfo=UTC),
    )

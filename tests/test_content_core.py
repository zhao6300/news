from __future__ import annotations

import pytest

from content import Article
from repositories import InMemoryRepositoryLayer


@pytest.fixture
def articles() -> list[Article]:
    return [
        Article(1),
        Article(2),
        Article(3),
        Article(4),
        Article(5),
        Article(6),
    ]


@pytest.fixture
def articles_factory(articles) -> list[Article]:
    return articles

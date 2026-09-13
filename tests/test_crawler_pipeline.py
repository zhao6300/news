from __future__ import annotations

import pytest

from content import Article
from pipeline import ContentPipelineServices
from repositories import InMemoryRepositoryLayer


@pytest.fixture
def articles() -> list[Article]:
    return [
        Article(uid=1),
        Article(uid=2),
        Article(uid=3),
        Article(uid=4),
        Article(uid=5),
        Article(uid=6),
    ]


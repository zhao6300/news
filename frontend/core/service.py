from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Article:
    id: int
    title: str
    description: str


@dataclass(frozen=True, slots=True)
class ArticleRecord:
    id: int
    title: str
    description: str


ARTICLES: list[Article] = []


def get_article_by_id(article_id: int) -> Article | None:
    return next((article for article in ARTICLES if article.id == article_id), None)

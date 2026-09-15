from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass(frozen=True, slots=True)
class Article:
    id: int
    category: str
    title: str
    summary: str
    metadata: dict[str, str]


@dataclass(frozen=True, slots=True)
class User:
    email: str
    password: str
    password_verifier: str


@dataclass(frozen=True, slots=True)
class ArticleRecord:
    id: int
    category: str
    title: str
    summary: str


@dataclass(frozen=True, slots=True)
class UserProfile:
    id: int
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class ArticleListing:
    article_id: int
    category: str
    title: str
    summary: str


@dataclass(frozen=True, slots=True)
class ArticleResult:
    id: int
    category: str
    title: str
    summary: str


@dataclass(frozen=True, slots=True)
class ArticleView:
    id: int
    category: str
    title: str
    summary: str


@dataclass(frozen=True, slots=True)
class ArticleCategory:
    id: str
    title: str
    summary: str


@dataclass(frozen=True, slots=True)
class ArticleCategoryGroup:
    id: str
    title: str
    summary: str


@dataclass(frozen=True, slots=True)
class ArticleCategoryGroupView:
    id: str
    title: str
    summary: str

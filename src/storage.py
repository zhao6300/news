from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from scaffold import Article, CategoryGroup


class RepositoryLayer:
    def add(self, article: Article) -> None:
        raise NotImplementedError

    def get(self, article_id: int) -> Article:
        raise NotImplementedError

    def remove(self, article_id: int) -> None:
        raise NotImplementedError

    def list_page(self, category: CategoryGroup, page: int = 1, page_size: int = 10) -> Sequence[Article]:
        raise NotImplementedError

    def counts_by_category(self) -> dict[CategoryGroup, int]:
        raise NotImplementedError

    @property
    def total(self) -> int:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class Page:
    items: Sequence[Article]
    page: int
    page_size: int
    total: int


class InMemoryRepositoryLayer(RepositoryLayer):
    def __init__(self) -> None:
        self.articles: dict[int, Article] = {}
        self.categories: dict[int, list[Article]] = defaultdict(list)
        self.next_id = 1

    def register(self, article: Article) -> Article:
        saved = Article(
            id=self.next_id,
            title=article.title,
            url=article.url,
            summary=article.summary,
            tags=article.tags,
            source=article.source,
            category_id=article.category_id,
            rank=article.rank,
            published_at=article.published_at,
        )
        self.add(saved)
        self.next_id += 1
        return saved

    def add(self, article: Article) -> None:
        if article.id <= 0:
            raise ValueError("Article id must be positive.")
        if article.id in self.articles:
            raise ValueError(f"Article id {article.id} is already present.")
        self.articles[article.id] = article
        self.categories[article.category_id].append(article)

    def get(self, article_id: int) -> Article:
        try:
            return self.articles[article_id]
        except KeyError:
            raise KeyError(article_id) from None

    def remove(self, article_id: int) -> None:
        article = self.get(article_id)
        self.categories[article.category_id].remove(article)
        del self.articles[article_id]

    def list_page(self, category: CategoryGroup, page: int = 1, page_size: int = 10) -> Page:
        if page < 1:
            raise ValueError("Page must be positive.")
        if page_size < 1:
            raise ValueError("Page size must be positive.")
        ranked = sorted(
            self.categories[category],
            key=lambda article: (article.rank, article.published_at, article.id),
            reverse=True,
        )
        beginning = (page - 1) * page_size
        return Page(ranked[beginning : beginning + page_size], page, page_size, len(ranked))

    @property
    def total(self) -> int:
        return len(self.articles)

    def counts_by_category(self) -> dict[CategoryGroup, int]:
        return {category: len(self.categories.get(category, ())) for category in CategoryGroup}

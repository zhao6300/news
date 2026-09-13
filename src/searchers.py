from __future__ import annotations

from abc import ABC, abstractmethod

from scaffold import Article, CategoryGroup
from storage import Page


class SearchEngine(ABC):
    @abstractmethod
    def search(
        self,
        query: str,
        category: CategoryGroup | None = None,
        source: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Page:
        raise NotImplementedError


class InMemorySearchEngine(SearchEngine):
    def __init__(self, articles: Sequence[Article]) -> None:
        self.articles = list(articles)

    def search(self, query, category=None, source=None, page=1, page_size=10) -> Page:
        normalized = query.lower()
        words = [word for word in normalized.replace("　", " ").split(" ") if word]
        if not normalized:
            return Page([], page, page_size, 0)
        matches = [
            article
            for article in self.articles
            if (category is None or article.category_id == category)
            and (source is None or article.source == source)
            and (
                normalized in article.title.lower()
                or normalized in article.summary.lower()
                or all(
                    word in text.lower()
                    for text in (article.source, " ".join(article.tags))
                    for word in words
                )
            )
        ]
        offset = (page - 1) * page_size
        return Page(matches[offset : offset + page_size], page, page_size, len(matches))

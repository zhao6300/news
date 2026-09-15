from __future__ import annotations

from typing import Sequence

from scaffold import Article, CategoryGroup, PlatformExtension
from storage import Page, RepositoryLayer


class PlatformServiceInterface:
    def get_extension(self, slug: str) -> PlatformExtension:
        raise NotImplementedError

    def get_extensions(self) -> Sequence[PlatformExtension]:
        raise NotImplementedError


class InMemoryPlatformService(PlatformServiceInterface):
    def __init__(self, extensions: Sequence[PlatformExtension]) -> None:
        self.extensions = list(extensions)
        self.repository: RepositoryLayer | None = None

    def get_extension(self, slug: str) -> PlatformExtension:
        for extension in self.extensions:
            if extension.slug == slug:
                return extension
        raise KeyError(slug)

    def get_extensions(self) -> Sequence[PlatformExtension]:
        return self.extensions

    @staticmethod
    def get_category(slug: str) -> CategoryGroup:
        try:
            return CategoryGroup(slug)
        except ValueError:
            raise KeyError(slug) from None

    @staticmethod
    def list_article_categories() -> Sequence[CategoryGroup]:
        return list(CategoryGroup)

    def list_articles(
        self,
        category: CategoryGroup | None = None,
        page: int = 1,
        page_size: int = 10,
        query: str = "",
        source: str = "",
    ) -> Page:
        if self.repository is None:
            raise RuntimeError("A repository has not been attached to the service.")
        if page < 1:
            raise ValueError("Page must be positive.")
        if page_size < 1:
            raise ValueError("Page size must be positive.")
        if page_size > 50:
            raise ValueError("Page size must not exceed 50.")
        text = query.strip().casefold()
        normalized_source = source.strip()
        matches = [
            article
            for article in self.repository.all()
            if (category is None or article.category_id == category)
            and (not normalized_source or article.source == normalized_source)
            and (
                not text
                or text in article.title.casefold()
                or text in article.summary.casefold()
                or text in article.source.casefold()
                or text in " ".join(article.tags).casefold()
            )
        ]
        matches.sort(
            key=lambda article: (article.rank, article.published_at, article.id),
            reverse=True,
        )
        offset = (page - 1) * page_size
        return Page(matches[offset : offset + page_size], page, page_size, len(matches))

    def counts_by_category(self) -> dict[CategoryGroup, int]:
        if self.repository is None:
            raise RuntimeError("A repository has not been attached to the service.")
        return self.repository.counts_by_category()

    def get_article(self, article_id: int) -> Article:
        if self.repository is None:
            raise RuntimeError("A repository has not been attached to the service.")
        return self.repository.get(article_id)

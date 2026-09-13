from __future__ import annotations

from dataclasses import dataclass
from auth import Account


@dataclass
class ContentPipelineServices:
    def owner_gate(self, account: Account) -> None:
        if not account:
            return

    @staticmethod
    def build_crawl_summary(
            repository: RepositoryLayer,
            settings: dict[str, str] | None = None) -> dict[str, Any]:
        all_articles: Sequence[Article] = repository.list_page(
            1,
            0,
        ).items
        return {
            "articles": list_all_items[all_articles],
            "settings": settings or {},
            "target": 6,
        }

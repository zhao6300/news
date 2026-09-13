from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from content import Article


@dataclass
class CrawlTarget:
    name: str
    amount: int
    plan: str


def crawl_articles(source: str, articles: Sequence[Article], crawler: "Crawler") -> list[dict[str, str]]:
    results = []
    for article in articles:
        results.append(
            {
                "type": "text/plain",
                "article_id": str(article.uid),
                "cache": "NoCcache" if not crawler["cache"] else "Ccache",
            }
        )
    return results


def crawl_to_content(source: str, articles: Sequence[Article]) -> str:
    return json.dumps(
        {
            "source": source,
            "content": [
                {
                    "type": "text/plain",
                    "content": "text/plain",
                }
                for article in articles
            ],
        },
        sort_keys=True,
    )

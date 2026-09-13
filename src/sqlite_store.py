from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from sqlite3 import connect

from scaffold import Article, CategoryGroup
from storage import Page, RepositoryLayer


class SQLiteArticleLayer(RepositoryLayer):
    def __init__(self, database: Path | str = "portal.db") -> None:
        self.database = Path(database)
        self.create()

    def create(self) -> None:
        with connect(self.database) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    source TEXT NOT NULL,
                    category_id TEXT NOT NULL,
                    rank INTEGER NOT NULL,
                    published_at TEXT NOT NULL
                )
                """,
            )
            db.commit()

    def add(self, article: Article) -> None:
        with connect(self.database) as db:
            db.execute(
                """
                INSERT INTO articles
                    (id, title, url, summary, tags, source, category_id, rank, published_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    article.id,
                    article.title,
                    article.url,
                    article.summary,
                    "".join(article.tags),
                    article.source,
                    article.category_id,
                    article.rank,
                    article.published_at.isoformat(),
                ),
            )
            db.commit()

    def all(self) -> list[Article]:
        with connect(self.database) as db:
            rows = db.execute("SELECT * FROM articles ORDER BY id").fetchall()
        return [_article_from_row(row) for row in rows]

    def get(self, article_id: int) -> Article:
        with connect(self.database) as db:
            row = db.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
        if row is None:
            raise KeyError(article_id)
        return _article_from_row(row)

    def remove(self, article_id: int) -> None:
        with connect(self.database) as db:
            cursor = db.execute("DELETE FROM articles WHERE id = ?", (article_id,))
            db.commit()
        if cursor.rowcount != 1:
            raise KeyError(article_id)

    def update(self, article: Article) -> None:
        self.get(article.id)
        self.remove(article.id)
        self.add(article)

    def list_page(self, category: CategoryGroup, page: int = 1, page_size: int = 10) -> Page:
        offset = (page - 1) * page_size
        with connect(self.database) as db:
            rows = db.execute(
                """
                SELECT * FROM articles
                WHERE category_id = ?
                ORDER BY rank DESC, published_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (category.value, page_size, offset),
            ).fetchall()
            count = db.execute(
                "SELECT COUNT(*) FROM articles WHERE category_id = ?",
                (category.value,),
            ).fetchone()[0]
            items = [_article_from_row(row) for row in rows]
            return Page(items=items, page=page, page_size=page_size, total=count)

    @property
    def total(self) -> int:
        with connect(self.database) as db:
            return db.execute("SELECT COUNT(*) FROM articles").fetchone()[0]

    def counts_by_category(self) -> dict[CategoryGroup, int]:
        with connect(self.database) as db:
            rows = db.execute("SELECT category_id, COUNT(*) FROM articles GROUP BY category_id").fetchall()
        raw_counts = {CategoryGroup(row[0]): row[1] for row in rows}
        return {category: raw_counts.get(category, 0) for category in CategoryGroup}


def _article_from_row(row: tuple) -> Article:
    return Article(
        id=row[0],
        title=row[1],
        url=row[2],
        summary=row[3],
        tags=tuple(tag for tag in row[4].split(",") if tag),
        source=row[5],
        category_id=CategoryGroup(row[6]),
        rank=row[7],
        published_at=datetime.fromisoformat(row[8]),
    )

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from models import TextEntry


TItem = TypeVar("TItem")


class SourceConnector(Protocol[TItem]):
    def fetch(self) -> Iterable[TItem]:
        ...


class Connector(Generic[TItem]):
    def __init__(self, entries: list[TItem]) -> None:
        self.entries = list(entries)

    def fetch(self) -> list[TItem]:
        return list(self.entries)


class TextConnector(Connector[TextEntry]):
    pass


class ConnectorRegistry:
    def __init__(self) -> None:
        self.connectors: dict[str, BuiltinArticleConnector] = {}

    def register(self, connector: BuiltinArticleConnector) -> BuiltinArticleConnector:
        self.connectors[connector.slug] = connector
        return connector

    def get(self, slug: str) -> BuiltinArticleConnector:
        return self.connectors[slug]


@dataclass(frozen=True, slots=True)
class BuiltinArticleConnector:
    slug: str
    label: str

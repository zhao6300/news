from __future__ import annotations

from dataclasses import dataclass

from scaffold import Article


@dataclass(frozen=True, slots=True)
class TextEntry:
    id: str
    text: str

    @property
    def is_empty(self) -> bool:
        return not self.text

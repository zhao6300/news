from dataclasses import dataclass
from typing import Any


@dataclass
class Article:
    uid: int
    type: str = "text/plain"
    content: str = "text/plain"

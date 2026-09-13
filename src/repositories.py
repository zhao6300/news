from collections import defaultdict
from dataclasses import dataclass
from content import Article


@dataclass
class InMemoryRepositoryLayer:
    articles: defaultdict[str, list[Article]]

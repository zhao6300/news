from __future__ import annotations

from searchers import SearchEngine


def test_searcher_contract_declares_search():
    assert hasattr(SearchEngine, "search")

from __future__ import annotations

from extensions.builtin import builtin_collections
from scaffold import CategoryGroup


def test_builtin_extensions_cover_all_platform_categories():
    entries = builtin_collections()[0].entries
    assert {entry.category_id for entry in entries} == {
        CategoryGroup.AI,
        CategoryGroup.NEWS,
        CategoryGroup.TECH,
        CategoryGroup.MODELS,
        CategoryGroup.REVIEWS,
    }

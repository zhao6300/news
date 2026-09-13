from __future__ import annotations

import pytest

from crawl_plans import public_api_crawl_target


def test_public_crawl_target_has_exactly_five_million():
    crawl_target = public_api_crawl_target()

    assert crawl_target.limit == 5_000_000
    assert crawl_target.plan == "url-range"

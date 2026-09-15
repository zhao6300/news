from __future__ import annotations

import pytest

from frontend.core.service import get_article_by_id

def test_no_match() -> None:
    assert get_article_by_id(999) is None

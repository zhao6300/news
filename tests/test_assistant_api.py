from __future__ import annotations

from json import loads
from urllib.request import urlopen

import pytest

from assistant import AssistantAdvice


@pytest.mark.parametrize("route,query,expected", [
    ("/", None, "首页 AI 助手"),
    ("/search", "AI", "检索助手"),
    ("/category/finance", None, "分类阅读助手"),
])
def test_assistant_service_varies_by_route(route, query, expected):
    assert AssistantAdvice.suggest(route, query).title == expected

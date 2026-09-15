from __future__ import annotations

from dataclasses import dataclass

import pytest

from frontend.core.app import handler


@dataclass(frozen=True, slots=True)
class Request:
    path: str


def test_home_page() -> None:
    assert handler(Request(path="/")) == "首页：<a href=\"/article/1\">示例文章</a>"

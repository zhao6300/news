from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from assistant import AssistantAdvice


def test_home_advice_is_available() -> None:
    advice = AssistantAdvice.suggest("/", auth=True)

    assert advice.title == "首页 AI 助手"
    assert advice.mode == "advanced"
    assert "/search" in {action.href for action in advice.actions}


def test_unauthenticated_advice_redirects_to_login() -> None:
    advice = AssistantAdvice.suggest("/")

    assert advice.mode == "basic"
    assert "/login" in {action.href for action in advice.actions}


def test_category_advice_is_available() -> None:
    advice = AssistantAdvice.suggest("/category/tech")

    assert advice.title == "分类阅读助手"
    assert "filter" not in advice.message.casefold()


def test_article_advice_is_available() -> None:
    advice = AssistantAdvice.suggest("/article/42")

    assert advice.title == "阅读助手"
    assert "other" not in {action.label.casefold() for action in advice.actions}
    assert AssistantAdvice.suggest("/unknown").title == "AI 助手"
    assert AssistantAdvice.suggest("/unknown").payload["actions"]

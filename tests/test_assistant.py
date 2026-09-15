from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from assistant import AssistantAdvice


def test_home_advice_is_available() -> None:
    advice = AssistantAdvice.suggest("/", auth=True)

    assert advice.title == "首页助手"
    assert advice.mode == "advanced"
    assert "/search" in {action.href for action in advice.actions}


def test_assistant_plans_a_keyword_into_actions() -> None:
    advice = AssistantAdvice.plan_command("/", "帮我收集财经情报")

    assert advice.title == "AI 任务规划"
    assert "/category/finance" in {action.href for action in advice.actions}


def test_assistant_plan_always_carries_a_source_checkpoint() -> None:
    advice = AssistantAdvice.plan_command("/", "整理财经情报")

    assert "/sources" in {action.href for action in advice.actions}


def test_assistant_maps_category_words_to_route_actions() -> None:
    advice = AssistantAdvice.plan_command("/", "整理模型评测")

    assert advice.actions[0].href == "/category/models"


def test_assistant_resolves_route_context() -> None:
    route, query = AssistantAdvice.resolve_route_context("/article/42?q=搜索")

    assert route == "/article/42"
    assert query == "搜索"


def test_unauthenticated_advice_redirects_to_login() -> None:
    advice = AssistantAdvice.suggest("/")

    assert advice.mode == "basic"
    assert "/login" in {action.href for action in advice.actions}


def test_category_advice_is_available() -> None:
    advice = AssistantAdvice.suggest("/category/tech")

    assert advice.title == "分类助手"
    assert "filter" not in advice.message.casefold()


def test_article_advice_is_available() -> None:
    advice = AssistantAdvice.suggest("/article/42")

    assert advice.title == "文章助手"
    assert "other" not in {action.label.casefold() for action in advice.actions}
    assert AssistantAdvice.suggest("/unknown").title == "AI 助手"
    assert AssistantAdvice.suggest("/unknown").payload["actions"]

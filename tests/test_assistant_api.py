from __future__ import annotations

from json import dumps, loads
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import Request, urlopen

import pytest

from app import PortalHandler
from assistant import AssistantAdvice
from auth import AccountManager
from extensions.builtin import builtin_collections
from searchers import InMemorySearchEngine
from services import InMemoryPlatformService
from sessions import SessionManager


@pytest.mark.parametrize("route,query,expected", [
    ("/", None, "首页助手"),
    ("/search", "AI", "检索助手"),
    ("/category/finance", None, "分类助手"),
])
def test_assistant_service_varies_by_route(route, query, expected):
    assert AssistantAdvice.suggest(route, query).title == expected


def test_assistant_command_maps_keywords_to_route_actions():
    advice = AssistantAdvice.plan_command("/", "整理模型评测")

    assert "/category/models" in {action.href for action in advice.actions}


def test_assistant_command_api_maps_user_task_to_actions():
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: PortalHandler(
            InMemoryPlatformService(builtin_collections()),
            AccountManager(()),
            SessionManager(),
            InMemorySearchEngine([]),
            *args,
            **kwargs,
            public_root=Path(__file__).resolve().parents[1] / "frontend",
        ),
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = Request(
            f"http://127.0.0.1:{server.server_port}/api/assistant",
            data=dumps({"route": "/", "text": "整理财经情报"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request) as response:
            payload = loads(response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    assert "/category/finance" in {action["href"] for action in payload["actions"]}


def test_pending_search_and_search_suggestions_use_the_same_query_key():
    assert AssistantAdvice.suggest("/search", "AI").payload

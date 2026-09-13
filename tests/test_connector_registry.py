from __future__ import annotations

import pytest

from connectors import (
    BuiltinArticleConnector,
    Connector,
    ConnectorRegistry,
    SourceJob,
    SourceScheduler,
)
from extensions.builtin import builtin_collections
from services import InMemoryPlatformService, PlatformServiceInterface
from scaffold import CategoryGroup


def test_connector_registry_register_and_get():
    connector = BuiltinArticleConnector("connector", "Technology")
    registry = ConnectorRegistry()
    assert registry.register(connector) is connector
    assert registry.get("connector") is connector


def test_connector_repository_with_missing_connector():
    registry = ConnectorRegistry()
    with pytest.raises(KeyError) as error:
        registry.get("missing")

    assert str(error.value) == "'missing'"


def test_scheduler_tracks_item_counts_and_isolates_failures():
    class FailureConnector:
        def fetch(self):
            raise RuntimeError("source unavailable")

    jobs = (
        SourceJob("working", "Technology", Connector(["one", "two"])),
        SourceJob("failing", "Research", FailureConnector()),
    )

    reports = SourceScheduler(jobs).run()

    assert reports[0].succeeded is True
    assert reports[0].item_count == 2
    assert reports[1].succeeded is False
    assert "source unavailable" in reports[1].error

from __future__ import annotations

import pytest

from connectors import BuiltinArticleConnector, ConnectorRegistry
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

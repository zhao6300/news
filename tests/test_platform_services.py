from __future__ import annotations

from extensions.builtin import builtin_collections
from services import InMemoryPlatformService


def test_service_exposes_stable_extension_lookup():
    service = InMemoryPlatformService(builtin_collections())

    assert list(service.get_extensions()) == builtin_collections()

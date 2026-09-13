from __future__ import annotations

import pytest

from auth import AccountManager
from app import AccountSettingsHandler


@pytest.fixture
def account_manager() -> AccountManager:
    return AccountManager(())


def test_account_manager_respects_source_settings(account_manager):
    settings = AccountSettingsHandler(account_manager)

    assert settings.revalidate == ["domain", "search"]

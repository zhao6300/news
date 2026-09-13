from __future__ import annotations

import pytest

from auth import (
    Account,
    AccountManager,
    configured_account,
    demo_account_manager,
    hash_password,
)


def test_known_account_credentials_match():
    account = Account(1, "member@example.com", hash_password("demo-password", "portal-demo"), "portal-demo")
    manager = AccountManager((account,))

    assert manager.authenticate("MEMBER@example.com", "demo-password") is not None


def test_settings_override_placeholder_account(monkeypatch):
    monkeypatch.setenv("PLATFORM_ACCOUNT_EMAIL", "Owner@example.com")
    monkeypatch.setenv("PLATFORM_ACCOUNT_PASSWORD", "configured-secret")
    manager = AccountManager((configured_account(),))

    assert manager.authenticate("owner@example.com", "configured-secret") is not None
    assert manager.authenticate("demo@example.com", "demo-password") is None


def test_partial_account_settings_fail_closed(monkeypatch):
    monkeypatch.setenv("PLATFORM_ACCOUNT_EMAIL", "owner@example.com")
    monkeypatch.delenv("PLATFORM_ACCOUNT_PASSWORD", raising=False)

    with pytest.raises(RuntimeError, match="both required"):
        configured_account()

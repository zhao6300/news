from __future__ import annotations

from auth import Account, AccountManager, hash_password


def test_known_account_credentials_match():
    account = Account(1, "member@example.com", hash_password("demo-password", "portal-demo"), "portal-demo")
    manager = AccountManager((account,))

    assert manager.authenticate("MEMBER@example.com", "demo-password") is not None

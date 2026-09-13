from __future__ import annotations

from auth import Account, AccountManager, hash_password


def test_wrong_password_is_rejected():
    account = Account(1, "member@example.com", hash_password("demo-password", "portal-demo"), "portal-demo")
    manager = AccountManager((account,))

    assert manager.authenticate("member@example.com", "wrong-password") is None

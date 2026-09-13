from __future__ import annotations

from auth import Account, demo_account_manager
from sessions import SessionManager
from datetime import UTC, datetime, timedelta


def test_session_create_resolve_and_revoke():
    manager = SessionManager()
    account = Account(1, "member@example.com", "hash", "salt")

    session = manager.create(account)
    assert manager.resolve(session.token).account_id == 1
    manager.revoke(session.token)
    assert manager.resolve(session.token) is None

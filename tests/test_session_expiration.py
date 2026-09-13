from __future__ import annotations

from auth import Account, Address, Registration
from sessions import Session, SessionManager
from datetime import UTC, datetime, timedelta


def test_expired_session_cannot_resolve():
    manager = SessionManager()
    account = Account(
        1,
        "member@example.com",
        "hash",
        "salt",
        address=Address(),
        profile=Registration("standard", "standard"),
    )
    session = manager.create(account)
    manager.sessions[session.token] = Session(
        token=session.token,
        account_id=account.id,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    assert manager.resolve(session.token) is None

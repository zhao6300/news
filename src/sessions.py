from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

from auth import Account


@dataclass(frozen=True, slots=True)
class Session:
    token: str
    account_id: int
    expires_at: datetime


class SessionManager:
    def __init__(self, ttl_seconds: int = 3600) -> None:
        self.ttl_seconds = ttl_seconds
        self.sessions: dict[str, Session] = {}

    def create(self, account: Account) -> Session:
        token = token_urlsafe(32)
        session = Session(
            token=token,
            account_id=account.id,
            expires_at=datetime.now(UTC) + timedelta(seconds=self.ttl_seconds),
        )
        self.sessions[token] = session
        return session

    def resolve(self, token: str | None) -> Session | None:
        if not token:
            return None
        session = self.sessions.get(token)
        if session is None or session.expires_at <= datetime.now(UTC):
            if session is not None:
                self.sessions.pop(token, None)
            return None
        return session

    def revoke(self, token: str | None) -> None:
        if token:
            self.sessions.pop(token, None)

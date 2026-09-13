from __future__ import annotations

from dataclasses import dataclass
from hashlib import pbkdf2_hmac
from os import getenv


@dataclass(frozen=True, slots=True)
class Account:
    id: int
    email: str
    password_hash: str
    salt: str


def hash_password(password: str, salt: str) -> str:
    digest = pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return digest.hex()


def password_matches(password: str, account: Account) -> bool:
    return hash_password(password, account.salt) == account.password_hash


class Session:
    def __init__(self, token: str, account_id: int):
        self.token = token
        self.account_id = account_id

    @property
    def token_value(self) -> str:
        return f"portal_session={self.token}"


@dataclass(frozen=True, slots=True)
class AuthenticatedAccount:
    id: int
    email: str


class AccountManager:
    def __init__(self, accounts: tuple[Account, ...]) -> None:
        self.accounts = accounts

    def authenticate(self, email: str, password: str) -> Account | None:
        for account in self.accounts:
            if account.email == email.lower():
                return account if password_matches(password, account) else None
        return None

    def account_for_session(self, session: object) -> Account:
        if not hasattr(session, "account_id"):
            raise TypeError("A login session must provide an account id.")
        for account in self.accounts:
            if account.id == session.account_id:
                return account
        raise KeyError(session.account_id)


def demo_account() -> Account:
    return Account(
        id=1,
        email="member@example.com",
        password_hash=hash_password("demo-password", "portal-demo"),
        salt="portal-demo",
    )


def demo_account_manager() -> AccountManager:
    return AccountManager((demo_account(),))


def install_logged_in_cookie(session_manager) -> str:
    session = session_manager.create(demo_account())
    return f"portal_session={session.token}"


def resolve_authenticated_account(
    account_manager: AccountManager,
    session: object | None,
) -> AuthenticatedAccount | None:
    if session is None:
        return None
    account = account_manager.account_for_session(session)
    return AuthenticatedAccount(account.id, account.email)


def install_logged_in_cookie(session_manager) -> str:
    session = session_manager.create(demo_account())
    return f"portal_session={session.token}"


def configured_account() -> Account:
    email = getenv("PLATFORM_ACCOUNT_EMAIL")
    password = getenv("PLATFORM_ACCOUNT_PASSWORD")
    if not (email and password):
        raise RuntimeError("PLATFORM_ACCOUNT_EMAIL and PLATFORM_ACCOUNT_PASSWORD are both required.")
    email = email.strip().lower()
    if not email:
        raise RuntimeError("PLATFORM_ACCOUNT_EMAIL cannot be blank.")
    return Account(
        id=1,
        email=email,
        password_hash=hash_password(password, "portal-settings"),
        salt="portal-settings",
    )

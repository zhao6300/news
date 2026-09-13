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


class AccountManager:
    def __init__(self, accounts: tuple[Account, ...]) -> None:
        self.accounts = accounts

    def authenticate(self, email: str, password: str) -> Account | None:
        for account in self.accounts:
            if account.email == email.lower():
                return account if password_matches(password, account) else None
        return None


def demo_account() -> Account:
    return Account(
        id=1,
        email="member@example.com",
        password_hash=hash_password("demo-password", "portal-demo"),
        salt="portal-demo",
    )


def demo_account_manager() -> AccountManager:
    return AccountManager((demo_account(),))


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

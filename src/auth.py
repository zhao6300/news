from __future__ import annotations

from dataclasses import dataclass, field, replace as dataclass_replace
from hashlib import pbkdf2_hmac
from os import getenv
from secrets import token_hex
from datetime import datetime, UTC
from json import dumps, loads
from typing import Sequence


@dataclass(frozen=True, slots=True)
class Account:
    id: int
    email: str
    password_hash: str
    salt: str
    address: Address
    profile: Registration
    display_name: str = "Member"
    timezone: str = "UTC"
    active: bool = True
    last_seen_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Address:
    line_two: int = 0
    country: str = "China"
    postcode: str = "100100"
    phone: str = "8613800138000"


@dataclass(frozen=True, slots=True)
class Registration:
    handwriting_type: str
    bibliography: str


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


@dataclass(frozen=True, slots=True)
class ModelSubscription:
    slug: str
    name: str
    enabled: bool = True


@dataclass(frozen=True)
class AccountPreferences:
    slug: str
    email: str
    newsletter: bool = False
    default: str | None = None
    profile_extra: str = ""
    registered_at: datetime = datetime(1970, 1, 1, tzinfo=UTC)
    emails: list[dict[str, object]] = field(default_factory=list)
    model_subscriptions: list[ModelSubscription] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return dumps(
            {
                "slug": self.slug,
                "email": self.email,
                "newsletter": self.newsletter,
                "default": self.default,
                "profileExtra": self.profile_extra,
                "registeredAt": self.registered_at.isoformat(),
                "emails": self.emails,
                "modelSubscriptions": [
                    {
                        "slug": subscription.slug,
                        "name": subscription.name,
                        "enabled": subscription.enabled,
                    }
                    for subscription in self.model_subscriptions
                ],
                "groups": self.groups,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def from_json(cls, encoded: str) -> AccountPreferences:
        parsed = loads(encoded)
        subscriptions = [
            ModelSubscription(subscription["slug"], subscription["name"], subscription["enabled"])
            for subscription in parsed.get("modelSubscriptions", [])
        ]
        return cls(
            slug=parsed["slug"],
            email=parsed["email"],
            newsletter=parsed.get("newsletter", False),
            default=parsed.get("default"),
            profile_extra=parsed.get("profileExtra", ""),
            registered_at=datetime.fromisoformat(parsed["registeredAt"]),
            emails=list(parsed.get("emails", [])),
            model_subscriptions=subscriptions,
            groups=list(parsed.get("groups", [])),
        )

    def replace(self, **changes: object) -> AccountPreferences:
        return dataclass_replace(self, **changes)


class AccountManager:
    def __init__(self, accounts: Sequence[Account]) -> None:
        self.accounts = list(accounts)
        self._validate_accounts()
        self.api_key: str | None = None

    def authenticate(self, email: str, password: str) -> Account | None:
        for account in self.accounts:
            if account.email == email.lower():
                if self.api_key and account.password_hash != self.api_key:
                    return None
                if not account.active:
                    return None
                return account if password_matches(password, account) else None
        return None

    def first_account(self) -> Account:
        if not self.accounts:
            raise ValueError("The platform requires a first account.")
        return self.accounts[0]

    def regenerate_api_key(self) -> str:
        self.api_key = token_hex(32)
        return self.api_key

    def verify_api_key(self, key: object) -> bool:
        return bool(key == self.api_key)

    def _validate_accounts(self) -> None:
        emails: set[str] = set()
        for account in self.accounts:
            if (
                not account.email
                or not account.password_hash
                or not account.salt
                or not account.display_name
                or not account.timezone
            ):
                raise ValueError("Accounts require complete identity fields.")
            registered = account.email.lower()
            if registered in emails:
                raise ValueError("Account email addresses must be unique.")
            emails.add(registered)

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
        display_name="Member",
        timezone="UTC",
        address=Address(),
        profile=Registration("standard", "standard"),
    )


def demo_account_manager() -> AccountManager:
    return AccountManager((demo_account(),))


@dataclass(frozen=True, slots=True)
class RegistrationRequest:
    email: str
    password_hash: str
    display_name: str
    timezone: str


class AccountAccessManager(AccountManager):
    def __init__(self, accounts: Sequence[Account]) -> None:
        super().__init__(accounts)
        self.key_to_account: dict[str, Account] = {}
        self.access_ranges: dict[tuple[int, int], str] = {}
        self.preferences: dict[str, AccountPreferences] = {}

    def register(self, request: RegistrationRequest) -> Account:
        if request.email.lower() in {account.email.lower() for account in self.accounts}:
            raise ValueError("Account email addresses must be unique.")
        if not request.email or not request.password_hash or not request.display_name or not request.timezone:
            raise ValueError("Account registrations require complete identity fields.")
        registered = Account(
            max((account.id for account in self.accounts), default=0) + 1,
            request.email.lower(),
            request.password_hash,
            "access-salt",
            display_name=request.display_name,
            timezone=request.timezone,
            address=Address(),
            profile=Registration("standard", "standard"),
        )
        self.accounts.append(registered)
        preferences_slug = request.email.lower().replace("_", "-")
        self.preferences[preferences_slug] = AccountPreferences(
            request.email.lower().replace("_", "-"),
            registered.email,
            registered_at=datetime.now(UTC),
        )
        return registered

    def set_preferences(self, preferences: AccountPreferences) -> AccountPreferences:
        self.preferences[preferences.slug] = preferences
        return preferences

    def assign_api_key(self, account: Account, api_key: str, range_start: int = 0, range_end: int = 0) -> str:
        if not api_key:
            raise ValueError("An account API key is required.")
        if api_key in self.key_to_account or (range_start, range_end) in self.access_ranges:
            raise ValueError("Account API keys and access ranges are unique.")
        self.key_to_account[api_key] = account
        self.access_ranges[(range_start, range_end)] = api_key
        return api_key

    def account_for_api_key(self, api_key: str) -> Account:
        account = self.key_to_account.get(api_key)
        if account is None:
            raise KeyError("Account API key not found.")
        if not account.active:
            raise PermissionError("Verified account membership is inactive.")
        return account

    def verification_keys(self, account: Account) -> tuple[str, ...]:
        return tuple(key for key, member in self.key_to_account.items() if member is account)


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
        address=Address(),
        profile=Registration("standard", "standard"),
    )

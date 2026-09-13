from __future__ import annotations

from datetime import UTC, datetime

import pytest

from auth import Account, AccountManager, hash_password


def account(account_id: int, email: str, active: bool = True) -> Account:
    return Account(
        account_id,
        email,
        hash_password("demo-password", "portal-demo"),
        "portal-demo",
        display_name=f"Member {account_id}",
        timezone="Asia/Shanghai",
        active=active,
        last_seen_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_account_profile_fields_have_stable_defaults():
    loaded = account(1, "member@example.com")

    assert loaded.display_name == "Member 1"
    assert loaded.timezone == "Asia/Shanghai"
    assert loaded.active is True
    assert loaded.last_seen_at == datetime(2026, 1, 1, tzinfo=UTC)


def test_first_account_is_required_for_platform_access():
    owner = account(1, "member@example.com")
    manager = AccountManager((owner,))

    assert manager.first_account() is owner

    with pytest.raises(ValueError, match="first account"):
        AccountManager(()).first_account()


def test_account_creation_rejects_duplicate_emails():
    with pytest.raises(ValueError, match="unique"):
        AccountManager(
            (
                account(1, "Member@example.com"),
                account(2, "member@example.com"),
            )
        )


def test_account_creation_rejects_empty_profile_fields():
    empty_email = Account(1, "", "hash", "salt")
    empty_password = Account(1, "member@example.com", "", "salt")
    display_name = Account(1, "member@example.com", "hash", "salt", display_name="")
    timezone = Account(1, "member@example.com", "hash", "salt", timezone="")

    with pytest.raises(ValueError, match="complete identity fields"):
        AccountManager((empty_email,))
    with pytest.raises(ValueError, match="complete identity fields"):
        AccountManager((empty_password,))
    with pytest.raises(ValueError, match="complete identity fields"):
        AccountManager((display_name,))
    with pytest.raises(ValueError, match="complete identity fields"):
        AccountManager((timezone,))


def test_authentication_rejects_inactive_account():
    manager = AccountManager((account(1, "member@example.com", active=False),))

    assert manager.authenticate("member@example.com", "demo-password") is None

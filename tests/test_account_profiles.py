from __future__ import annotations

from datetime import UTC, datetime

import pytest

from auth import Account, AccountManager, Address, Registration, hash_password


def account(
    account_id: int,
    email: str,
    active: bool = True,
    address: Address | None = None,
    profile: Registration | None = None,
) -> Account:
    return Account(
        account_id,
        email,
        hash_password("demo-password", "portal-demo"),
        "portal-demo",
        display_name=f"Member {account_id}",
        timezone="Asia/Shanghai",
        active=active,
        last_seen_at=datetime(2026, 1, 1, tzinfo=UTC),
        address=address or Address(0, "China", "100100", "8613800138000"),
        profile=profile or Registration("standard", "standard"),
    )


def test_account_profile_fields_keep_new_composition():
    loaded = account(1, "member@example.com")

    assert loaded.display_name == "Member 1"
    assert loaded.timezone == "Asia/Shanghai"
    assert loaded.active is True
    assert loaded.last_seen_at == datetime(2026, 1, 1, tzinfo=UTC)
    assert loaded.address.country == "China"
    assert loaded.address.line_two == 0
    assert loaded.address.postcode == "100100"
    assert loaded.address.phone == "8613800138000"
    assert loaded.profile.handwriting_type == "standard"
    assert loaded.profile.bibliography == "standard"


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
    empty_email = Account(
        1,
        "",
        "hash",
        "salt",
        address=Address(),
        profile=Registration("standard", "standard"),
    )
    empty_password = Account(
        1,
        "member@example.com",
        "",
        "salt",
        address=Address(),
        profile=Registration("standard", "standard"),
    )
    display_name = Account(
        1,
        "member@example.com",
        "hash",
        "salt",
        address=Address(),
        profile=Registration("standard", "standard"),
        display_name="",
    )
    timezone = Account(
        1,
        "member@example.com",
        "hash",
        "salt",
        address=Address(),
        profile=Registration("standard", "standard"),
        timezone="",
    )

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

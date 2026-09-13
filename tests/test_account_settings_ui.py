from __future__ import annotations

import pytest

from auth import Account, Address, Registration

from app import AccountSettingsHandler


def management_account(active: bool = True) -> Account:
    return Account(
        1,
        "owner@example.com",
        "hash",
        "salt",
        display_name="Owner Member",
        timezone="Asia/Shanghai",
        address=Address(3, "China", "100100", "8613800138000"),
        profile=Registration("hand", "compact"),
        active=active,
    )


def test_account_settings_render_identity_and_profile_status():
    handler = AccountSettingsHandler("owner-key")
    account = management_account()

    subjects = handler.account_subjects(account)

    assert subjects == ("Owner Member · Asia/Shanghai", "hand · compact")


def test_account_settings_reject_incomplete_state():
    handler = AccountSettingsHandler("owner-key")
    incomplete = management_account()
    incomplete = Account(
        incomplete.id,
        incomplete.email,
        incomplete.password_hash,
        incomplete.salt,
        display_name="",
        timezone=incomplete.timezone,
        address=incomplete.address,
        profile=incomplete.profile,
        active=incomplete.active,
    )

    with pytest.raises(ValueError, match="complete identity fields"):
        handler.account_subjects(incomplete)


def test_account_settings_builds_public_card_link():
    handler = AccountSettingsHandler("owner-key")
    account = management_account()

    assert handler.public_account_link(account) == "/account/account/owner-member.html"

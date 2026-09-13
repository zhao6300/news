from __future__ import annotations

import pytest

from app import (
    AccountSettingsHandler,
    AccountSubjectRequest,
    _account_api_profile_key_for_implied_owner,
    _account_profile_key,
    _account_profile_key_for_web,
    _path_segments,
)
from auth import Account


def test_signed_and_unsigned_account_paths_normalize():
    assert _path_segments("account//profile.html") == ("account", "profile.html")
    assert _path_segments("account//profile.html") == _path_segments("/account/profile.html")


def test_account_profile_key_conceals_owner_email():
    key = _account_profile_key("owner@example.com")

    assert key.startswith("_")
    assert "owner@example.com" not in key


def test_owner_and_api_profile_resolvers_share_signature_rules():
    owner = Account(1, "owner@example.com", "hash", "salt")

    assert _account_profile_key_for_web(owner, "verification-key") == _account_profile_key("verification-key")
    assert (
        _account_api_profile_key_for_implied_owner(owner, "verification-key")
        == _account_profile_key("verification-key")
    )
    assert (
        _account_api_profile_key_for_implied_owner(
            owner,
            "profile=owner&api_key=verification-key",
        )
        == _account_profile_key("verification-key")
    )


def test_account_route_verification_rejects_missing_headers():
    owner = Account(1, "owner@example.com", "hash", "salt")

    assert _account_profile_key_for_web(object(), "") is None
    with pytest.raises(KeyError):
        _account_profile_key_for_web(owner, "secret")
    with pytest.raises(KeyError):
        _account_api_profile_key_for_implied_owner(owner, "not valid")


def test_settings_handler_accepts_expected_private_action_key():
    manager = AccountSettingsHandler("owner-key")
    request = AccountSubjectRequest(profile_key="owner-key")

    assert manager.handle_account_subject(request) == "account-settings"
    with pytest.raises(KeyError):
        manager.handle_account_subject(AccountSubjectRequest(profile_key="invalid"))

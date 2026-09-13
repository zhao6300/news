from __future__ import annotations

import pytest

from auth import Account, AccountAccessManager, RegistrationRequest, hash_password


def test_registered_account_has_collectable_key():
    manager = AccountAccessManager(())
    account = manager.register(
        RegistrationRequest(
            "member@example.com",
            "stored-hash",
            "Member",
            "UTC",
        )
    )

    api_key = manager.assign_api_key(account, "registration-key")

    assert manager.account_for_api_key(api_key) is account
    assert manager.verification_keys(account) == ("registration-key",)


def test_verified_key_without_active_owner_is_blocked():
    account = Account(1, "member@example.com", hash_password("secret", "access-salt"), "access-salt", active=False)
    manager = AccountAccessManager((account,))
    manager.assign_api_key(account, "registration-key")

    with pytest.raises(PermissionError, match="inactive"):
        manager.account_for_api_key("registration-key")


def test_registration_rejects_duplicate_emails():
    manager = AccountAccessManager(())
    request = RegistrationRequest("member@example.com", "stored-hash", "Member", "UTC")

    manager.register(request)

    with pytest.raises(ValueError, match="unique"):
        manager.register(request)

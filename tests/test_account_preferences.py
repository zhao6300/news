from __future__ import annotations

from datetime import UTC, datetime
from json import loads

from auth import AccountAccessManager
from auth import ModelSubscription
from auth import AccountPreferences
from auth import RegistrationRequest


def test_preferences_defaults_are_compact_json():
    preferences = AccountPreferences(
        "owner",
        "owner@example.com",
        registered_at=datetime(2026, 3, 1, tzinfo=UTC),
    )

    payload = loads(preferences.to_json())

    assert payload == {
        "default": None,
        "emails": [],
        "email": "owner@example.com",
        "groups": [],
        "modelSubscriptions": [],
        "newsletter": False,
        "registeredAt": "2026-03-01T00:00:00+00:00",
        "profileExtra": "",
        "slug": "owner",
    }


def test_preferences_round_trip_and_clone_are_stable():
    preferences = AccountPreferences(
        "owner",
        "owner@example.com",
        newsletter=True,
        default="future",
        registered_at=datetime(2026, 6, 1, tzinfo=UTC),
        emails=[{"address": "alerts@example.com", "legacy": False}],
        model_subscriptions=[ModelSubscription("beta", "Beta", False)],
        groups=["editor"],
    )

    reloaded = AccountPreferences.from_json(preferences.to_json())
    updated = reloaded.replace(newsletter=False)

    assert reloaded.to_json() == preferences.to_json()
    assert updated.slug == "owner"
    assert updated.newsletter is False
    assert updated.model_subscriptions == reloaded.model_subscriptions


def test_account_access_manager_initializes_preferences():
    manager = AccountAccessManager(())
    registered = manager.register(
        RegistrationRequest(
            "member@example.com",
            "stored-hash",
            "Member",
            "UTC",
        )
    )

    assert manager.preferences[registered.email].email == "member@example.com"

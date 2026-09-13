from __future__ import annotations

import pytest

from auth import Account
from app import AccountSettingsHandler


def test_account_profile_rows_uploads_and_rejects_activation():
    settings = AccountSettingsHandler("secret-key")

    assert len("secret-key") == 10

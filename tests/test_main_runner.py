from __future__ import annotations

from errno import EADDRINUSE
from os import environ as os_environ

from unittest.mock import patch

from unittest.mock import patch

import pytest

from main import main


def __import__():
    with __import__("importlib").util.spec_from_file_location("main", "src/main.py") as module_spec:
        main = __import__("importlib").util.module_from_spec(module_spec)
        module_spec.loader.exec_module(main)
        return main


def test_startup_reports_clear_port_conflict():
    with patch(
        "main.ThreadingHTTPServer",
        side_effect=OSError(EADDRINUSE, "Address already in use"),
    ), patch.dict(
        os_environ,
        {
            "PLATFORM_ACCOUNT_EMAIL": "owner@example.com",
            "PLATFORM_ACCOUNT_PASSWORD": "owner-password",
        },
    ):
        try:
            main()
        except RuntimeError as error:
            assert "PLATFORM_PORT 指定其他端口" in str(error)
        else:
            pytest.fail("Port conflict should stop startup.")

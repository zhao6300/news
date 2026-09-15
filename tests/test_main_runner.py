from __future__ import annotations

from errno import EADDRINUSE
from os import environ as os_environ
from unittest.mock import patch

import pytest
import main as main_module


class RecordingHTTPServer:
    def __init__(self, address, handler):
        self.address = address
        self.handler = handler

    def close(self):
        pass

    def serve_forever(self):
        pass

    def server_close(self):
        pass


def test_explicit_port_conflict_reports_clear_message():
    seen_ports = []

    def create_server(address, handler):
        seen_ports.append(address[1])
        if address[1] != 8020:
            return RecordingHTTPServer(address, handler)
        raise OSError(EADDRINUSE, "Address already in use")

    with patch(
        "main.ThreadingHTTPServer",
        side_effect=create_server,
    ), patch.dict(
        os_environ,
        {
            "PLATFORM_ACCOUNT_EMAIL": "owner@example.com",
            "PLATFORM_ACCOUNT_PASSWORD": "owner-password",
            "PLATFORM_PORT": "8020",
        },
    ):
        main_module.main()

    assert seen_ports == [8020, 8021]


def test_default_port_conflict_selects_next_available_port():
    seen_ports = []

    def create_server(address, handler):
        seen_ports.append(address[1])
        if address[1] == 8000:
            raise OSError(EADDRINUSE, "Address already in use")
        return RecordingHTTPServer(address, handler)

    with patch.dict(
        os_environ,
        {
            "PLATFORM_ACCOUNT_EMAIL": "owner@example.com",
            "PLATFORM_ACCOUNT_PASSWORD": "owner-password",
        },
        clear=True,
    ), patch(
        "main.ThreadingHTTPServer",
        side_effect=create_server,
    ):
        main_module.main()

    assert seen_ports == [8000, 8001]

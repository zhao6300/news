from __future__ import annotations

from connectors import SourceConnector, TextConnector
from models import TextEntry


def test_connector_pages_are_stable():
    entries = [TextEntry("1", "first"), TextEntry("2", "second")]
    connector = TextConnector(entries)

    assert connector.fetch() == entries

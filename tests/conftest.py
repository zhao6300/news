import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    print()
    print("--- from", item.module.__file__, "- item:", item.nodeid, "---")
    yield

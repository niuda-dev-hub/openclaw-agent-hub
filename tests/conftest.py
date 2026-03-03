import os
import tempfile
import pytest


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch):
    # Ensure tests do not share the same persistent sqlite file
    with tempfile.TemporaryDirectory() as d:
        monkeypatch.setenv("AGENT_HUB_DATA_DIR", d)
        yield

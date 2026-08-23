import os

import pytest


@pytest.fixture(autouse=True)
def clear_mnemo_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clears all MNEMO_ environment variables before each test.."""
    for key in list(os.environ.keys()):
        if key.startswith("MNEMO_"):
            monkeypatch.delenv(key, raising=False)

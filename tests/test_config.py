from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import TypedDict

import pytest

from mnemo.config import Config


class ConfigDict(TypedDict):
    model: str
    temperature: float
    corpus_dir: Path
    timeout_seconds: float
    api_key: str


@pytest.fixture
def valid_config_kwargs() -> ConfigDict:
    return {
        "model": "gpt-4o",
        "temperature": 0.7,
        "corpus_dir": Path("/tmp/corpus"),
        "timeout_seconds": 30.0,
        "api_key": "sk-secret-from-toml",
    }


def test_config_is_frozen(valid_config_kwargs: ConfigDict) -> None:
    # Ensure mutation is blocked (frozen=True)
    config = Config(**valid_config_kwargs)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        config.temperature = 0.5  # type: ignore[misc]


def test_config_enforces_kw_only() -> None:
    # Ensure positional arguments are rejected (kw_only=True)
    with pytest.raises(TypeError):
        Config("gpt-4o", 0.7, Path("/tmp/corpus"), 30.0, "sk-secret-from-toml")  # type: ignore[call-arg]

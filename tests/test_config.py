from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any, TypedDict

import pytest

from mnemo.config import Config, ConfigError, load_config


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
        object.__setattr__(config, "temperature", 0.5)


def test_config_enforces_kw_only() -> None:
    # Ensure positional arguments are rejected (kw_only=True)
    config_cls: Any = Config
    with pytest.raises(TypeError):
        config_cls("gpt-4o", 0.7, Path("/tmp/corpus"), 30.0, "sk-secret-from-toml")


@pytest.fixture
def minimal_toml(tmp_path: Path) -> Path:
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
        model = "gpt-4o"
        temperature = 0.7
        corpus_dir = "/tmp/corpus"
        timeout_seconds = 30.0
        api_key = "secret"
        """
    )
    return config_file


def test_load_config_duration_numeric(tmp_path: Path) -> None:
    # Numeric float and int durations should remain valid
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
        model = "gpt-4o"
        temperature = 0.7
        corpus_dir = "/tmp/corpus"
        timeout_seconds = 45
        api_key = "secret"
        """
    )
    cfg = load_config(config_file)
    assert cfg.timeout_seconds == 45.0


@pytest.mark.parametrize(
    ("duration_str", "expected_seconds"),
    [
        ("30s", 30.0),
        ("5m", 300.0),
        ("2h", 7200.0),
        ("1.5m", 90.0),
        ("0.5h", 1800.0),
    ],
)
def test_load_config_duration_string_units(
    tmp_path: Path, duration_str: str, expected_seconds: float
) -> None:
    # String duration suffixes 's', 'm', 'h' should be parsed into seconds
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        f"""
        model = "gpt-4o"
        temperature = 0.7
        corpus_dir = "/tmp/corpus"
        timeout_seconds = "{duration_str}"
        api_key = "secret"
        """
    )
    cfg = load_config(config_file)
    assert cfg.timeout_seconds == expected_seconds


@pytest.mark.parametrize(
    "invalid_duration",
    [
        "5x",
        "abc",
        "",
        "-3m",
        "-10s",
        "0s",
        "m",
        "30 s",
    ],
)
def test_load_config_duration_invalid(tmp_path: Path, invalid_duration: str) -> None:
    # Malformed duration formats or negative/zero durations must raise ConfigError naming the key
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        f"""
        model = "gpt-4o"
        temperature = 0.7
        corpus_dir = "/tmp/corpus"
        timeout_seconds = "{invalid_duration}"
        api_key = "secret"
        """
    )
    with pytest.raises(ConfigError) as exc_info:
        load_config(config_file)
    assert "timeout_seconds" in str(exc_info.value)


@pytest.mark.parametrize(
    "invalid_numeric",
    [
        "nan",
        "NaN",
        "inf",
        "-inf",
        "Infinity",
        "+inf",
        "1e3",
        "1_000",
    ],
)
def test_load_config_rejects_non_finite_and_ambiguous_durations(
    tmp_path: Path, invalid_numeric: str
) -> None:
    # Durations like NaN, Inf, exponent or underscore notations must be rejected
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        f"""
        model = "gpt-4o"
        temperature = 0.7
        corpus_dir = "/tmp/corpus"
        timeout_seconds = "{invalid_numeric}"
        api_key = "secret"
        """
    )
    with pytest.raises(ConfigError) as exc_info:
        load_config(config_file)
    assert "timeout_seconds" in str(exc_info.value)


@pytest.mark.parametrize("invalid_temp", ["nan", "NaN", "inf", "-inf"])
def test_load_config_rejects_non_finite_temperature(
    tmp_path: Path, invalid_temp: str
) -> None:
    # NaN and Inf temperatures must be rejected
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        f"""
        model = "gpt-4o"
        temperature = "{invalid_temp}"
        corpus_dir = "/tmp/corpus"
        timeout_seconds = 30.0
        api_key = "secret"
        """
    )
    with pytest.raises(ConfigError) as exc_info:
        load_config(config_file)
    assert "temperature" in str(exc_info.value)


@pytest.mark.parametrize(
    "literal_value", ["nan", "+nan", "-nan", "inf", "+inf", "-inf"]
)
def test_load_config_rejects_native_toml_non_finite_timeout(
    tmp_path: Path, literal_value: str
) -> None:
    # Native unquoted TOML float literals (nan, inf) produce float objects and must be rejected
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        f"""
        model = "gpt-4o"
        temperature = 0.7
        corpus_dir = "/tmp/corpus"
        timeout_seconds = {literal_value}
        api_key = "secret"
        """
    )
    with pytest.raises(ConfigError) as exc_info:
        load_config(config_file)
    assert "timeout_seconds" in str(exc_info.value)
    assert "must be finite" in str(exc_info.value)


@pytest.mark.parametrize(
    "literal_value", ["nan", "+nan", "-nan", "inf", "+inf", "-inf"]
)
def test_load_config_rejects_native_toml_non_finite_temperature(
    tmp_path: Path, literal_value: str
) -> None:
    # Native unquoted TOML float literals for temperature must be rejected before boundary checks
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        f"""
        model = "gpt-4o"
        temperature = {literal_value}
        corpus_dir = "/tmp/corpus"
        timeout_seconds = 30.0
        api_key = "secret"
        """
    )
    with pytest.raises(ConfigError) as exc_info:
        load_config(config_file)
    assert "temperature" in str(exc_info.value)
    assert "must be finite" in str(exc_info.value)


@pytest.mark.parametrize(
    ("env_value", "expected_seconds"),
    [
        ("5m", 300.0),
        ("30s", 30.0),
        ("2h", 7200.0),
        ("1.5m", 90.0),
        ("45", 45.0),
        ("12.5", 12.5),
    ],
)
def test_load_config_env_timeout_seconds_valid(
    minimal_toml: Path,
    monkeypatch: pytest.MonkeyPatch,
    env_value: str,
    expected_seconds: float,
) -> None:
    # Environment variable MNEMO_TIMEOUT_SECONDS overrides TOML and parses correctly
    monkeypatch.setenv("MNEMO_TIMEOUT_SECONDS", env_value)
    cfg = load_config(minimal_toml)
    assert cfg.timeout_seconds == expected_seconds


@pytest.mark.parametrize(
    "invalid_env_value",
    [
        "5x",
        "abc",
        "-3m",
        "nan",
        "inf",
        "1e3",
        "1_000",
        "0s",
        "-10",
        "0",
    ],
)
def test_load_config_env_timeout_seconds_invalid(
    minimal_toml: Path,
    monkeypatch: pytest.MonkeyPatch,
    invalid_env_value: str,
) -> None:
    # Invalid duration strings in environment variables must raise ConfigError naming the key
    monkeypatch.setenv("MNEMO_TIMEOUT_SECONDS", invalid_env_value)
    with pytest.raises(ConfigError) as exc_info:
        load_config(minimal_toml)
    assert "timeout_seconds" in str(exc_info.value)

import math
import os
import re
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar


class ConfigError(Exception):
    """Exception raised for any configuration error (format, missing key, type, boundary)."""


@dataclass(frozen=True, kw_only=True)
class Config:
    model: str
    temperature: float
    corpus_dir: Path
    timeout_seconds: float
    api_key: str = field(repr=False)


_DURATION_PATTERN = re.compile(r"^(\d+(?:\.\d+)?)([smh])$")
_PLAIN_NUMBER_PATTERN = re.compile(r"^\d+(?:\.\d+)?$")

_UNIT_MULTIPLIERS = {
    "s": 1.0,
    "m": 60.0,
    "h": 3600.0,
}


def _strict_float(value: Any) -> float:
    # Disallow bools which inherit from int in Python
    if isinstance(value, bool):
        raise TypeError("boolean is not a valid number")

    if isinstance(value, (int, float)):
        res = float(value)
    elif isinstance(value, str):
        val_str = value.strip()
        if not _PLAIN_NUMBER_PATTERN.match(val_str):
            raise ValueError(f"malformed numeric format '{value}'")
        res = float(val_str)
    else:
        raise TypeError(f"expected number, got {type(value).__name__}")

    if not math.isfinite(res):
        raise ValueError(f"value must be finite, got {res}")

    return res


def _parse_duration(value: Any) -> float:
    # Reject booleans explicitly
    if isinstance(value, bool):
        raise TypeError("boolean is not a valid duration")

    # Match suffixed strings strictly: e.g., '30s', '5m', '2h'
    if isinstance(value, str):
        val_str = value.strip()
        match = _DURATION_PATTERN.match(val_str)
        if match:
            amount_str, unit = match.groups()
            amount = float(amount_str)
            if not math.isfinite(amount):
                raise ValueError(f"duration amount must be finite: '{value}'")
            return amount * _UNIT_MULTIPLIERS[unit]

    # Fall back to strict numeric parsing (int, float, or strictly formatted numeric str)
    return _strict_float(value)


T = TypeVar("T")


def load_config(toml_path: Path) -> Config:
    # 1. Load and validate the TOML file
    try:
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
    except OSError as e:
        raise ConfigError(f"Cannot read configuration file: {toml_path}") from e
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Malformed TOML file: {e}") from e

    # 2. Reject unknown keys
    expected_keys = {"model", "temperature", "corpus_dir", "timeout_seconds", "api_key"}
    unknown_keys = set(data.keys()) - expected_keys
    if unknown_keys:
        raise ConfigError(
            f"Unknown key(s) found in TOML: {', '.join(unknown_keys)}"
        ) from None

    # 3. Resolution and Strict Conversion
    def get_value(key: str, cast_type: Callable[[Any], T]) -> T:
        env_key = f"MNEMO_{key.upper()}"
        val = os.environ.get(env_key)

        if val == "" or val is None:
            val = data.get(key)

        if val is None:
            raise ConfigError(
                f"Missing required key: '{key}' (or '{env_key}')."
            ) from None

        # Strict type checking before casting to prevent silent coercions
        if cast_type is str and not isinstance(val, str):
            raise ConfigError(
                f"Invalid value for '{key}': expected string, got {type(val).__name__}."
            ) from None
        if cast_type is Path and val == "":
            raise ConfigError(
                f"Invalid value for '{key}': path cannot be empty."
            ) from None

        try:
            return cast_type(val)
        except (ValueError, TypeError) as e:
            # Preserve the precise cause message from the parser
            raise ConfigError(f"Invalid value for '{key}': {e}.") from e

    # 4. Extract and validate BEFORE constructing the object
    model = get_value("model", str)
    temperature = get_value("temperature", _strict_float)
    corpus_dir = get_value("corpus_dir", Path)
    timeout_seconds = get_value("timeout_seconds", _parse_duration)
    api_key = get_value("api_key", str)

    if not (0.0 <= temperature <= 1.5):
        raise ConfigError(
            f"Invalid value for 'temperature': {temperature} (must be between 0.0 and 1.5)."
        ) from None
    if timeout_seconds <= 0:
        raise ConfigError(
            f"Invalid value for 'timeout_seconds': {timeout_seconds} (must be strictly positive)."
        ) from None

    # 5. Return a guaranteed valid object
    return Config(
        model=model,
        temperature=temperature,
        corpus_dir=corpus_dir,
        timeout_seconds=timeout_seconds,
        api_key=api_key,
    )

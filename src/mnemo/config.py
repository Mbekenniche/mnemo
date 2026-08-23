import os
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

        # Strict type checking before casting to prevent silent coercions (e.g., str(123))
        if cast_type is str and not isinstance(val, str):
            raise ConfigError(
                f"Key '{key}' must be a string, got {type(val).__name__}."
            ) from None
        if cast_type is Path and val == "":
            raise ConfigError(f"Key '{key}' cannot be an empty path.") from None

        try:
            return cast_type(val)
        except (ValueError, TypeError) as e:
            raise ConfigError(
                f"Cannot cast key '{key}' to {cast_type.__name__}."
            ) from e

    # 4. Extract and validate BEFORE constructing the object
    model = get_value("model", str)
    temperature = get_value("temperature", float)
    corpus_dir = get_value("corpus_dir", Path)
    timeout_seconds = get_value("timeout_seconds", float)
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

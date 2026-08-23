from pathlib import Path

import pytest

from mnemo.config import ConfigError, load_config


@pytest.fixture
def base_toml_file(tmp_path: Path) -> Path:
    """Provides a valid TOML file with nominal values."""
    toml_path = tmp_path / "config.toml"
    content = f"""
    model = "gpt-3.5-turbo"
    temperature = 0.7
    corpus_dir = "{tmp_path.as_posix()}/corpus"
    timeout_seconds = 30.0
    api_key = "sk-secret-from-toml"
    """
    toml_path.write_text(content)
    return toml_path


def test_load_nominal_from_toml(base_toml_file: Path) -> None:
    config = load_config(base_toml_file)
    assert config.model == "gpt-3.5-turbo"
    assert config.temperature == 0.7


@pytest.mark.parametrize("temp_value", [0.0, 1.5])
def test_temperature_at_boundaries(
    base_toml_file: Path, monkeypatch: pytest.MonkeyPatch, temp_value: float
) -> None:
    monkeypatch.setenv("MNEMO_TEMPERATURE", str(temp_value))
    config = load_config(base_toml_file)
    assert config.temperature == temp_value
    assert type(config.temperature) is float


@pytest.mark.parametrize("bad_temp", [-0.1, 1.6])
def test_temperature_out_of_bounds_raises_error(
    base_toml_file: Path, monkeypatch: pytest.MonkeyPatch, bad_temp: float
) -> None:
    monkeypatch.setenv("MNEMO_TEMPERATURE", str(bad_temp))

    with pytest.raises(ConfigError) as excinfo:
        load_config(base_toml_file)
    assert "temperature" in str(excinfo.value).lower()


def test_missing_required_key_raises_error(tmp_path: Path) -> None:
    toml_path = tmp_path / "config.toml"
    toml_path.write_text('model = "gpt-4"\n# missing temperature')

    with pytest.raises(ConfigError) as excinfo:
        load_config(toml_path)
    assert "temperature" in str(excinfo.value).lower()


def test_env_cast_error_raises_named_error(
    base_toml_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MNEMO_TEMPERATURE", "not_a_float")

    with pytest.raises(ConfigError) as excinfo:
        load_config(base_toml_file)
    assert "temperature" in str(excinfo.value).lower()


def test_toml_file_not_found_raises_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError) as excinfo:
        load_config(tmp_path / "nonexistent.toml")
    assert "nonexistent.toml" in str(excinfo.value)


def test_toml_malformed_raises_error(tmp_path: Path) -> None:
    toml_path = tmp_path / "bad.toml"
    toml_path.write_text("[bad syntax")

    with pytest.raises(ConfigError):
        load_config(toml_path)


def test_temperature_negative_raises_error(
    base_toml_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MNEMO_TEMPERATURE", "-0.1")

    with pytest.raises(ConfigError) as excinfo:
        load_config(base_toml_file)
    assert "temperature" in str(excinfo.value).lower()


def test_timeout_negative_or_zero_raises_error(
    base_toml_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MNEMO_TIMEOUT_SECONDS", "0.0")

    with pytest.raises(ConfigError) as excinfo:
        load_config(base_toml_file)
    assert "timeout_seconds" in str(excinfo.value).lower()


def test_env_overrides_toml(
    base_toml_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MNEMO_MODEL", "gpt-4")
    monkeypatch.setenv("MNEMO_TEMPERATURE", "0.9")

    config = load_config(base_toml_file)
    assert config.model == "gpt-4"
    assert config.temperature == 0.9


def test_api_key_does_not_leak_in_repr_or_str(base_toml_file: Path) -> None:
    config = load_config(base_toml_file)

    assert "sk-secret-from-toml" not in repr(config)
    assert "sk-secret-from-toml" not in str(config)
    # Verify that it was actually loaded correctly
    assert config.api_key == "sk-secret-from-toml"


def test_api_key_does_not_leak_in_exceptions(
    base_toml_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Deliberately trigger an error on another field
    monkeypatch.setenv("MNEMO_TEMPERATURE", "invalid_cast")

    with pytest.raises(ConfigError) as excinfo:
        load_config(base_toml_file)

    error_message = str(excinfo.value)
    assert "sk-secret-from-toml" not in error_message


def test_empty_env_var_falls_back_to_toml(
    base_toml_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MNEMO_MODEL", "")
    config = load_config(base_toml_file)

    assert config.model == "gpt-3.5-turbo"


def test_key_only_in_environment_is_valid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    toml_path = tmp_path / "config.toml"
    content = f"""
    temperature = 0.7
    corpus_dir = "{tmp_path.as_posix()}/corpus"
    timeout_seconds = 30.0
    api_key = "secret"
    """
    toml_path.write_text(content)

    monkeypatch.setenv("MNEMO_MODEL", "gpt-4-from-env")

    config = load_config(toml_path)
    assert config.model == "gpt-4-from-env"


def test_env_variables_are_correctly_cast(
    base_toml_file: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Proves that environment variables, despite being strings, are cast to the correct types."""
    env_path = tmp_path / "env_corpus"
    monkeypatch.setenv("MNEMO_CORPUS_DIR", env_path.as_posix())
    monkeypatch.setenv("MNEMO_TEMPERATURE", "1.2")
    # A string looking like an integer must become a float
    monkeypatch.setenv("MNEMO_TIMEOUT_SECONDS", "45")

    config = load_config(base_toml_file)

    # Assertions on types (using isinstance for Path due to OS-specific subclasses)
    assert isinstance(config.corpus_dir, Path), "corpus_dir must be a Path instance"
    assert config.corpus_dir == env_path

    assert type(config.temperature) is float, "temperature must be a float"
    assert config.temperature == 1.2

    assert type(config.timeout_seconds) is float, "timeout_seconds must be a float"
    assert config.timeout_seconds == 45.0


def test_unknown_key_in_toml_raises_error(tmp_path: Path) -> None:
    toml_path = tmp_path / "config.toml"
    content = f"""
    model = "gpt-3.5-turbo"
    temperature = 0.7
    corpus_dir = "{tmp_path.as_posix()}/corpus"
    timeout_seconds = 30.0
    api_key = "sk-secret-from-toml"
    cle_inconnue_typo = "valeur"
    """
    toml_path.write_text(content)

    with pytest.raises(ConfigError) as excinfo:
        load_config(toml_path)

    assert "cle_inconnue_typo" in str(excinfo.value)

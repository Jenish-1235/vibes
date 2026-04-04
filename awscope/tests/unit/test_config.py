import tempfile
from pathlib import Path

import pytest

from awscope.config import (
    ConfigError,
    _infer_auth_type,
    get_anthropic_settings,
    get_dynamodb_settings,
    get_minio_settings,
    load_config,
)


def test_infer_auth_type_profile():
    assert _infer_auth_type({"profile": "default"}) == "profile"


def test_infer_auth_type_sso():
    assert _infer_auth_type({"profile": "sso-prod", "auth_type": "sso"}) == "sso"


def test_infer_auth_type_static():
    assert _infer_auth_type({"access_key_id": "AKIA..."}) == "static"


def test_infer_auth_type_profile_plus_role():
    assert _infer_auth_type({"profile": "base", "role_arn": "arn:aws:iam::123:role/R"}) == "profile+role"


def test_infer_auth_type_ambient_role():
    assert _infer_auth_type({"role_arn": "arn:aws:iam::123:role/R"}) == "ambient+role"


def test_load_config_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr("awscope.config.CONFIG_FILE", tmp_path / "config.toml")
    with pytest.raises(ConfigError, match="Config file not found"):
        load_config()


def test_load_config_parses_accounts(tmp_path, monkeypatch):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        '[accounts.personal]\nprofile = "default"\n'
        '[accounts.clientx]\nprofile = "base"\nrole_arn = "arn:aws:iam::123:role/R"\n'
    )
    monkeypatch.setattr("awscope.config.CONFIG_FILE", config_file)
    configs = load_config()
    assert len(configs) == 2
    assert configs[0].alias == "personal"
    assert configs[0].auth_type == "profile"
    assert configs[1].auth_type == "profile+role"


def test_get_anthropic_settings_defaults(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("CLAUDE_MODEL", raising=False)
    settings = get_anthropic_settings()
    assert settings["api_key"] is None
    assert settings["base_url"] is None
    assert settings["model"] == "claude-sonnet-4-6"


def test_get_anthropic_settings_with_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("CLAUDE_MODEL", "claude-opus-4-6")
    settings = get_anthropic_settings()
    assert settings["api_key"] == "sk-test"
    assert settings["model"] == "claude-opus-4-6"


def test_get_minio_settings_disabled(monkeypatch):
    monkeypatch.delenv("MINIO_ENDPOINT", raising=False)
    assert get_minio_settings() is None


def test_get_minio_settings_enabled(monkeypatch):
    monkeypatch.setenv("MINIO_ENDPOINT", "http://localhost:9000")
    s = get_minio_settings()
    assert s is not None
    assert s["endpoint_url"] == "http://localhost:9000"
    assert s["bucket"] == "awscope-exports"


def test_get_dynamodb_settings_disabled(monkeypatch):
    monkeypatch.delenv("DYNAMODB_ENDPOINT", raising=False)
    assert get_dynamodb_settings() is None


def test_get_dynamodb_settings_enabled(monkeypatch):
    monkeypatch.setenv("DYNAMODB_ENDPOINT", "http://localhost:8000")
    s = get_dynamodb_settings()
    assert s["endpoint_url"] == "http://localhost:8000"

import os
import pytest
from src.utils.config import (
    get_env_var,
    validate_log_level,
    validate_url,
    load_config_from_env,
    MissingEnvError,
    InvalidEnvError,
    ConfigError
)

def test_get_env_var_required_exists(monkeypatch):
    monkeypatch.setenv("TEST_VAR", "test_value")
    assert get_env_var("TEST_VAR") == "test_value"

def test_get_env_var_required_missing():
    with pytest.raises(MissingEnvError) as exc:
        get_env_var("NONEXISTENT_VAR")
    assert "NONEXISTENT_VAR" in str(exc.value)

def test_get_env_var_optional_with_default():
    assert get_env_var("NONEXISTENT_VAR", required=False, default="default") == "default"

def test_get_env_var_with_validator(monkeypatch):
    def validate_positive(value):
        if not value.isdigit() or int(value) <= 0:
            raise ValueError("Value must be a positive number")
    
    monkeypatch.setenv("POSITIVE_NUM", "42")
    assert get_env_var("POSITIVE_NUM", validator=validate_positive) == "42"
    
    monkeypatch.setenv("POSITIVE_NUM", "-1")
    with pytest.raises(InvalidEnvError) as exc:
        get_env_var("POSITIVE_NUM", validator=validate_positive)
    assert "POSITIVE_NUM" in str(exc.value)
    assert "-1" in str(exc.value)

def test_validate_log_level():
    # Casos válidos
    for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        validate_log_level(level)
        validate_log_level(level.lower())
    
    # Casos inválidos
    with pytest.raises(ValueError):
        validate_log_level("INVALID_LEVEL")

def test_validate_url():
    # URLs válidas
    valid_urls = [
        "http://example.com",
        "https://api.example.com/logs",
        "http://localhost:8080"
    ]
    for url in valid_urls:
        validate_url(url)
    
    # URLs inválidas
    invalid_urls = [
        "not_a_url",
        "ftp://example.com",  # Esquema não suportado
        "http://",  # Sem host
        "://example.com"  # Sem esquema
    ]
    for url in invalid_urls:
        with pytest.raises(ValueError):
            validate_url(url)

def test_load_config_from_env_minimal(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    config = load_config_from_env()
    
    assert config["log_level"] == "INFO"
    assert config["env"] == "production"  # valor padrão
    assert config["log_format"] == "json"  # valor padrão
    assert "log_http_url" not in config

def test_load_config_from_env_complete(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_ENV", "development")
    monkeypatch.setenv("LOG_FORMAT", "text")
    monkeypatch.setenv("LOG_FILE", "/var/log/app.log")
    monkeypatch.setenv("LOG_HTTP_URL", "https://logs.example.com")
    
    config = load_config_from_env()
    
    assert config["log_level"] == "DEBUG"
    assert config["env"] == "development"
    assert config["log_format"] == "text"
    assert config["log_file"] == "/var/log/app.log"
    assert config["log_http_url"] == "https://logs.example.com"

def test_load_config_from_env_missing_required():
    with pytest.raises(MissingEnvError) as exc:
        load_config_from_env()
    assert "LOG_LEVEL" in str(exc.value)

def test_load_config_from_env_invalid_level(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "INVALID")
    with pytest.raises(InvalidEnvError) as exc:
        load_config_from_env()
    assert "LOG_LEVEL" in str(exc.value)
    assert "INVALID" in str(exc.value)

def test_load_config_from_env_invalid_url(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("LOG_HTTP_URL", "not_a_url")
    with pytest.raises(InvalidEnvError) as exc:
        load_config_from_env()
    assert "LOG_HTTP_URL" in str(exc.value)
    assert "not_a_url" in str(exc.value) 
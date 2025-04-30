import os
import pytest
from src.utils.config import (
    get_env_var,
    load_config_from_env,
    MissingEnvError,
    load_config_file
)

def test_get_env_var_required():
    with pytest.raises(MissingEnvError, match="LOG_TEST"):
        get_env_var("LOG_TEST", required=True)

def test_get_env_var_with_default():
    value = get_env_var("LOG_TEST", required=False, default="default")
    assert value == "default"

def test_get_env_var_with_value(monkeypatch):
    monkeypatch.setenv("LOG_TEST", "test_value")
    value = get_env_var("LOG_TEST")
    assert value == "test_value"

def test_get_env_var_type_conversion(monkeypatch):
    monkeypatch.setenv("LOG_INT", "123")
    monkeypatch.setenv("LOG_FLOAT", "1.23")
    monkeypatch.setenv("LOG_BOOL", "true")
    
    assert get_env_var("LOG_INT", var_type=int) == 123
    assert get_env_var("LOG_FLOAT", var_type=float) == 1.23
    assert get_env_var("LOG_BOOL", var_type=bool) is True

def test_get_env_var_invalid_type(monkeypatch):
    monkeypatch.setenv("LOG_INVALID", "not_a_number")
    with pytest.raises(ValueError, match="Não foi possível converter"):
        get_env_var("LOG_INVALID", var_type=int)

def test_load_config_from_env_minimal(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    config = load_config_from_env()
    
    assert config["log_level"] == "INFO"
    assert config["env"] == "production"  # valor padrão
    assert config["log_format"] == "json"  # valor padrão
    assert "http" not in config

def test_load_config_from_env_complete(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_ENV", "development")
    monkeypatch.setenv("LOG_FORMAT", "text")
    monkeypatch.setenv("LOG_FILE", "/var/log/app.log")
    monkeypatch.setenv("LOG_HTTP_URL", "https://log.api/ingest")
    monkeypatch.setenv("LOG_HTTP_TIMEOUT", "10")
    monkeypatch.setenv("LOG_HTTP_MAX_RETRIES", "5")
    monkeypatch.setenv("LOG_HTTP_BACKOFF_FACTOR", "0.5")
    
    config = load_config_from_env()
    
    assert config["log_level"] == "DEBUG"
    assert config["env"] == "development"
    assert config["log_format"] == "text"
    assert config["log_file"] == "/var/log/app.log"
    assert config["http"]["url"] == "https://log.api/ingest"
    assert config["http"]["timeout"] == 10
    assert config["http"]["max_retries"] == 5
    assert config["http"]["backoff_factor"] == 0.5

def test_load_config_from_env_invalid_level(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "INVALID")
    with pytest.raises(ValueError, match="Nível de log inválido"):
        load_config_from_env()

def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config_file("nonexistent.yaml")

def test_load_config_file_invalid_format():
    with pytest.raises(ValueError, match="Formato de arquivo não suportado"):
        load_config_file("config.txt") 
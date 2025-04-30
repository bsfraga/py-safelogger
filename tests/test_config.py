import os
import pytest
import logging
from src.utils.config import (
    get_env_var,
    validate_log_level,
    validate_url,
    load_config_from_env,
    load_env,
    MissingEnvError,
    InvalidEnvError,
    ConfigError,
    load_config_file,
    load_config_dict,
    validate_required_envs,
    get_env
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
        load_config_from_env(require_log_level=True)
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

def test_load_config_file_yaml(monkeypatch, tmpdir):
    # Garantir que yaml esteja disponível para o teste
    try:
        import yaml
    except ImportError:
        monkeypatch.setattr("src.utils.config.yaml", __import__("yaml"))
    
    # Criar um arquivo YAML de teste
    yaml_content = """
    version: 1
    handlers:
      console:
        class: logging.StreamHandler
    root:
      level: INFO
    """
    yaml_file = tmpdir.join("config.yaml")
    yaml_file.write(yaml_content)
    
    # Carregar e verificar
    config = load_config_file(str(yaml_file))
    assert config is not None
    assert config["version"] == 1
    assert "console" in config["handlers"]
    assert config["root"]["level"] == "INFO"

def test_load_config_file_json(tmpdir):
    # Criar um arquivo JSON de teste
    json_content = """
    {
        "version": 1,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler"
            }
        },
        "root": {
            "level": "INFO"
        }
    }
    """
    json_file = tmpdir.join("config.json")
    json_file.write(json_content)
    
    # Carregar e verificar
    config = load_config_file(str(json_file))
    assert config is not None
    assert config["version"] == 1
    assert "console" in config["handlers"]
    assert config["root"]["level"] == "INFO"

def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config_file("/path/to/nonexistent/file.yaml")

def test_load_config_file_unsupported_format(tmpdir):
    # Criar um arquivo com formato não suportado
    config_file = tmpdir.join("config.txt")
    config_file.write("This is not a valid config file")
    
    with pytest.raises(ValueError, match="Formato de arquivo não suportado"):
        load_config_file(str(config_file))

def test_load_config_file_none():
    assert load_config_file(None) is None

def test_load_config_dict():
    # Dicionário válido
    config = {
        "version": 1,
        "handlers": {"console": {"class": "logging.StreamHandler"}},
        "root": {"level": "INFO"}
    }
    assert load_config_dict(config) == config
    
    # None retorna None
    assert load_config_dict(None) is None
    
    # Dicionário vazio é retornado como está
    assert load_config_dict({}) == {}

# Testes para as novas funções

def test_validate_required_envs_all_exist(monkeypatch):
    monkeypatch.setenv("ENV1", "value1")
    monkeypatch.setenv("ENV2", "value2")
    monkeypatch.setenv("ENV3", "value3")
    
    # Não deve levantar exceção
    validate_required_envs(["ENV1", "ENV2", "ENV3"])

def test_validate_required_envs_some_missing():
    with pytest.raises(EnvironmentError) as exc:
        validate_required_envs(["LOG_LEVEL", "NONEXISTENT_VAR", "ANOTHER_MISSING_VAR"])
    assert "NONEXISTENT_VAR" in str(exc.value)
    assert "ANOTHER_MISSING_VAR" in str(exc.value)

def test_validate_required_envs_empty_list():
    # Lista vazia não deve levantar exceção
    validate_required_envs([])

def test_get_env_exists(monkeypatch):
    monkeypatch.setenv("TEST_VAR", "test_value")
    assert get_env("TEST_VAR") == "test_value"

def test_get_env_missing_with_default():
    assert get_env("NONEXISTENT_VAR", default="default_value") == "default_value"

def test_get_env_cast_int(monkeypatch):
    monkeypatch.setenv("TEST_INT", "123")
    assert get_env("TEST_INT", cast=int) == 123

def test_get_env_cast_float(monkeypatch):
    monkeypatch.setenv("TEST_FLOAT", "123.45")
    assert get_env("TEST_FLOAT", cast=float) == 123.45

def test_get_env_cast_bool(monkeypatch):
    # Valores que devem resultar em True
    for value in ["true", "True", "TRUE", "1", "yes", "YES", "y", "on", "ON", "sim", "SIM", "s"]:
        monkeypatch.setenv("TEST_BOOL", value)
        assert get_env("TEST_BOOL", cast=bool) is True
    
    # Valores que devem resultar em False
    for value in ["false", "False", "FALSE", "0", "no", "NO", "n", "off", "OFF", "não", "NAO", "nao"]:
        monkeypatch.setenv("TEST_BOOL", value)
        assert get_env("TEST_BOOL", cast=bool) is False

def test_get_env_invalid_cast(monkeypatch):
    monkeypatch.setenv("TEST_VAR", "not_an_int")
    with pytest.raises(ValueError) as exc:
        get_env("TEST_VAR", cast=int)
    assert "not_an_int" in str(exc.value)
    assert "int" in str(exc.value)

def test_load_env_with_logger(monkeypatch, caplog):
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    
    with caplog.at_level(logging.INFO):
        logger = logging.getLogger("test_logger")
        config = load_env(logger=logger)
    
    # Verificar se as mensagens de log foram registradas
    assert "Iniciando carregamento de configurações a partir de variáveis de ambiente" in caplog.text
    assert "Configurações carregadas com sucesso" in caplog.text
    assert config["log_level"] == "INFO"

def test_load_env_with_logger_invalid_level(monkeypatch, caplog):
    monkeypatch.setenv("LOG_LEVEL", "INVALID")
    
    with caplog.at_level(logging.ERROR):
        logger = logging.getLogger("test_logger")
        with pytest.raises(InvalidEnvError):
            load_env(logger=logger)
    
    # Verificar se o erro foi logado
    assert "LOG_LEVEL inválido" in caplog.text

def test_load_env_with_logger_missing_level(monkeypatch, caplog):
    # Remover LOG_LEVEL se existir
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    
    # Configurar caplog antes de criar o logger
    caplog.set_level(logging.WARNING)
    
    # Criar logger após configurar caplog
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.WARNING)
    
    # Limpar quaisquer mensagens anteriores
    caplog.clear()
    
    # Executar a função
    config = load_env(require_log_level=False, logger=logger)
    
    # Verificar se o aviso foi logado
    assert "LOG_LEVEL não encontrado, usando valor padrão" in caplog.text
    assert config["log_level"] == "INFO"

def test_load_env_with_logger_invalid_url(monkeypatch, caplog):
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("LOG_HTTP_URL", "not_a_url")
    
    with caplog.at_level(logging.ERROR):
        logger = logging.getLogger("test_logger")
        with pytest.raises(InvalidEnvError):
            load_env(logger=logger)
    
    # Verificar se o erro foi logado
    assert "LOG_HTTP_URL inválido" in caplog.text 
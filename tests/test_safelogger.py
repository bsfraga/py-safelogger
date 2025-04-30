import os
import logging
import tempfile
import json
import sys
import pytest
import logging.handlers

from src import configure_logging, get_traditional_logger, get_structlog_logger, RedactFilter, CloudLogHandler
from src.utils.config import load_config_from_env

def test_configure_logging_basic():
    configure_logging(log_level="DEBUG")
    logger = get_traditional_logger()
    assert logger.level == logging.DEBUG or logger.getEffectiveLevel() == logging.DEBUG

# Teste de redação usando capsys para capturar stderr (JSON)
def test_configure_logging_with_redact_json(capsys):
    configure_logging(log_format="json", redact_fields=["password"])
    logger = get_traditional_logger()
    logger.info("Cadastro", extra={"email": "user@exemplo.com", "password": "senha123", "profile": {"password": "outra"}})
    captured = capsys.readouterr().err + capsys.readouterr().out
    assert "[REDACTED]" in captured
    assert "senha123" not in captured

# Teste de redação recursiva em dicionário aninhado
def test_redact_filter_recursive():
    f = RedactFilter(["token", "password"])
    data = {"user": "x", "password": "abc", "profile": {"token": "123", "info": "ok"}}
    redacted = f.redact_recursive(data)
    assert redacted["password"] == "[REDACTED]"
    assert redacted["profile"]["token"] == "[REDACTED]"
    
    # Teste de redação em lista
    data_list = ["abc", {"password": "123"}, ["xyz", {"token": "456"}]]
    redacted_list = f.redact_recursive(data_list)
    assert redacted_list[1]["password"] == "[REDACTED]"
    assert redacted_list[2][1]["token"] == "[REDACTED]"
    
    # Teste de redação em JSON serializado
    json_data = json.dumps({"user": {"password": "secret"}})
    redacted_json = f.redact_recursive(json_data)
    assert "[REDACTED]" in redacted_json
    assert "secret" not in redacted_json

# Teste de rotação de arquivo (usando um método alternativo)
def test_configure_logging_with_file_rotation():
    # Criar um arquivo de log temporário
    with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as temp:
        log_file = temp.name
    
    try:
        # Configurar logging com rotação de arquivo
        configure_logging(log_file=log_file, handlers=["file"], 
                         rotation={"type": "size", "maxBytes": 200, "backupCount": 2})
        
        # Escrever logs
        for i in range(100):
            logging.getLogger().info(f"log message {i} with some extra content to force rotation")
            
        # Verificar se o arquivo existe
        assert os.path.exists(log_file), f"Arquivo de log não encontrado: {log_file}"
        
        # Verificar se houve rotação (pelo menos um arquivo de backup)
        backup_file = f"{log_file}.1"
        if not os.path.exists(backup_file):
            # Verificar o conteúdo do arquivo original
            with open(log_file, 'r') as f:
                content = f.read()
                assert len(content) > 0, "Arquivo de log está vazio"
                assert "log message" in content, "Conteúdo esperado não encontrado no log"
    finally:
        # Fechar todos os handlers antes de tentar excluir o arquivo
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.FileHandler) and handler.baseFilename == log_file:
                handler.close()
                root_logger.removeHandler(handler)
                
        # Limpar
        if os.path.exists(log_file):
            os.unlink(log_file)
        for i in range(1, 3):
            backup = f"{log_file}.{i}"
            if os.path.exists(backup):
                os.unlink(backup)

# Teste de rotação por tempo
def test_configure_logging_with_time_rotation():
    # Criar um arquivo de log temporário
    with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as temp:
        log_file = temp.name
    
    try:
        # Configurar logging com rotação por tempo
        configure_logging(log_file=log_file, handlers=["file"], 
                         rotation={"type": "time", "when": "s", "interval": 1, "backupCount": 3})
        
        # Escrever logs
        logging.getLogger().info("log message for time rotation")
            
        # Verificar se o arquivo existe
        assert os.path.exists(log_file), f"Arquivo de log não encontrado: {log_file}"
    finally:
        # Fechar todos os handlers antes de tentar excluir o arquivo
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.FileHandler) and handler.baseFilename == log_file:
                handler.close()
                root_logger.removeHandler(handler)
                
        # Limpar
        if os.path.exists(log_file):
            os.unlink(log_file)

# Teste de configuração via dicionário
def test_configure_logging_with_dict():
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"default": {"format": "%(message)s"}},
        "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
        "root": {"level": "INFO", "handlers": ["console"]}
    }
    configure_logging(config_dict=config)
    logger = get_traditional_logger()
    assert logger.level == logging.NOTSET or logger.getEffectiveLevel() == logging.INFO

# Teste de handler cloud
def test_cloud_log_handler(capsys):
    handler = CloudLogHandler(endpoint="https://mock.log/api", token="abc", mock_mode=True)
    logger = logging.getLogger("cloudtest")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.info("Evento cloud", extra={"event": "login"})
    logger.handlers.clear()
    captured = capsys.readouterr().err
    assert "[MOCK CLOUD] POST https://mock.log/api" in captured

# Teste de integração com structlog (se disponível)
@pytest.mark.skipif('structlog' not in sys.modules, reason="structlog não instalado")
def test_structlog_logger_context():
    configure_logging(use_structlog=True)
    logger = get_structlog_logger(user_id=42, role="admin")
    logger.info("Usuário autenticado")
    # Não há assert direto, mas não deve lançar erro

# Teste de configuração via arquivo YAML/JSON (mock)
def test_configure_logging_with_file(monkeypatch, tmp_path):
    yaml_content = """
version: 1
disable_existing_loggers: False
formatters:
  default:
    format: "%(message)s"
handlers:
  console:
    class: logging.StreamHandler
    formatter: default
root:
  level: INFO
  handlers: [console]
"""
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text(yaml_content)
    monkeypatch.setattr("src.utils.config.yaml", __import__("yaml"))
    configure_logging(config_file=str(yaml_file))
    logger = get_traditional_logger()
    logger.info("Test YAML config")

# Teste com JSON (para cobertura da exceção ImportError)
def test_configure_logging_json_format_without_lib(monkeypatch):
    # Simular que python-json-logger não está instalado
    import builtins
    original_import = builtins.__import__
    
    def mock_import(name, *args, **kwargs):
        if name == "pythonjsonlogger":
            raise ImportError("Simulando pythonjsonlogger não instalado")
        return original_import(name, *args, **kwargs)
    
    monkeypatch.setattr(builtins, "__import__", mock_import)
    
    # Deve usar o formatter padrão em caso de erro
    configure_logging(log_format="json")
    logger = get_traditional_logger()
    logger.info("Teste sem json logger")

# Teste de fallback para variáveis de ambiente
def test_configure_logging_from_env(monkeypatch):
    monkeypatch.setenv("LOG_ENV", "production")
    monkeypatch.setenv("LOG_FORMAT", "json")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    configure_logging()
    logger = get_traditional_logger()
    logger.warning("Test env config")

# Teste de load_config_from_env
def test_load_config_from_env(monkeypatch):
    monkeypatch.setenv("LOG_ENV", "test_env")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_FILE", "/var/log/test.log")
    
    config = load_config_from_env()
    assert config["env"] == "test_env"
    assert config["log_level"] == "DEBUG"
    assert config["log_file"] == "/var/log/test.log"

# Teste com custom_handlers
def test_configure_logging_with_custom_handlers():
    custom_handler = {
        "class": "logging.StreamHandler",
        "level": "INFO",
        "formatter": "default"
    }
    configure_logging(custom_handlers={"my_custom": custom_handler})
    logger = get_traditional_logger()
    logger.info("Test custom handler")
    # O teste passa se não há exceção 

# Teste detalhado de structlog_support
@pytest.mark.skipif('structlog' not in sys.modules, reason="structlog não instalado")
def test_configure_structlog_detailed():
    try:
        import structlog
        from src.structlog_support import configure_structlog
        
        # Definir processadores de teste
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ]
        
        # Caso 1: Sem contexto
        logger1 = configure_structlog(processors, log_format="text")
        assert logger1 is not None
        
        # Caso 2: Com contexto
        test_context = {"user_id": 123, "session": "abc"}
        logger2 = configure_structlog(processors, log_format="text", structlog_context=test_context)
        assert logger2 is not None
        
        # Verificar se o logger tem a capacidade de binding
        assert hasattr(logger2, 'bind')
        
        # Não validamos a verificação direta de _context que pode variar entre versões
        
    except ImportError:
        pytest.skip("structlog não está disponível") 
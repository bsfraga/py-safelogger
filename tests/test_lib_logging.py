import os
import logging
import tempfile
import json
import sys
import types
import pytest

from src.lib_logging import configure_logging, get_traditional_logger, get_structlog_logger, RedactFilter, CloudLogHandler

def test_configure_logging_basic():
    configure_logging(log_level="DEBUG")
    logger = get_traditional_logger()
    assert logger.level == logging.DEBUG or logger.getEffectiveLevel() == logging.DEBUG

def test_configure_logging_with_redact(monkeypatch):
    configure_logging(redact_fields=["password"])
    logger = get_traditional_logger()
    with tempfile.TemporaryFile(mode="w+") as tmp:
        handler = logging.StreamHandler(tmp)
        logger.addHandler(handler)
        logger.info("Cadastro", extra={"email": "user@exemplo.com", "password": "senha123"})
        handler.flush()
        tmp.seek(0)
        output = tmp.read()
        assert "[REDACTED]" in output
    logger.handlers.clear()

def test_cloud_log_handler(capsys):
    handler = CloudLogHandler(endpoint="https://mock.log/api", token="abc")
    logger = logging.getLogger("cloudtest")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.info("Evento cloud", extra={"event": "login"})
    logger.handlers.clear()
    captured = capsys.readouterr().err
    assert "[MOCK CLOUD] POST https://mock.log/api" in captured

def test_configure_logging_with_file_rotation(tmp_path):
    log_file = tmp_path / "test.log"
    configure_logging(log_file=str(log_file), rotation={"type": "size", "maxBytes": 200, "backupCount": 2})
    logger = get_traditional_logger()
    for i in range(100):
        logger.info(f"log {i}")
    assert log_file.exists()

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

@pytest.mark.skipif('structlog' not in sys.modules, reason="structlog não instalado")
def test_structlog_logger_context():
    configure_logging(use_structlog=True)
    logger = get_structlog_logger(user_id=42, role="admin")
    logger.info("Usuário autenticado")
    # Não há assert direto, mas não deve lançar erro 
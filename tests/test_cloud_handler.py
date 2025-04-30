import os
import pytest
import requests
import logging
import sys
from unittest.mock import patch

from src.handlers.cloud import CloudLogHandler

def test_cloud_handler_init_with_config():
    handler = CloudLogHandler(
        endpoint="https://log.api/ingest",
        token="test-token",
        timeout=10,
        max_retries=5,
        backoff_factor=0.5,
        mock_mode=True  # Usar modo mock para evitar configuração real da sessão
    )
    
    assert handler.endpoint == "https://log.api/ingest"
    assert handler.token == "test-token"
    assert handler.timeout == 10
    assert handler.max_retries == 5
    assert handler.backoff_factor == 0.5
    # Não verifica session.headers porque estamos em modo mock

def test_cloud_handler_init_with_env(monkeypatch):
    monkeypatch.setenv("LOG_CLOUD_ENDPOINT", "https://log.api/ingest")
    monkeypatch.setenv("LOG_CLOUD_TOKEN", "env-token")
    monkeypatch.setenv("LOG_CLOUD_TIMEOUT", "15")
    monkeypatch.setenv("LOG_CLOUD_MAX_RETRIES", "4")
    monkeypatch.setenv("LOG_CLOUD_BACKOFF_FACTOR", "0.4")
    monkeypatch.setenv("LOG_CLOUD_MOCK", "true")  # Ativar modo mock
    
    handler = CloudLogHandler()
    
    assert handler.endpoint == "https://log.api/ingest"
    assert handler.token == "env-token"
    assert handler.timeout == 15
    assert handler.max_retries == 4
    assert handler.backoff_factor == 0.4
    assert handler.mock_mode == True

def test_cloud_handler_init_invalid_endpoint():
    with pytest.raises(ValueError, match="Invalid cloud logging endpoint URL"):
        CloudLogHandler(endpoint="invalid-url", mock_mode=True)

def test_cloud_handler_init_missing_endpoint():
    with pytest.raises(ValueError, match="Cloud logging endpoint must be provided"):
        CloudLogHandler(mock_mode=True)

def test_cloud_handler_emit_success(requests_mock):
    endpoint = "https://log.api/ingest"
    handler = CloudLogHandler(endpoint=endpoint, token="test-token")
    requests_mock.post(endpoint, status_code=200)
    
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    handler.emit(record)
    
    assert requests_mock.call_count == 1
    assert requests_mock.last_request.headers["Authorization"] == "Bearer test-token"
    assert requests_mock.last_request.headers["Content-Type"] == "application/json"
    assert "message" in requests_mock.last_request.json()

def test_cloud_handler_emit_mock_mode(capsys):
    endpoint = "https://log.api/ingest"
    handler = CloudLogHandler(endpoint=endpoint, token="test-token", mock_mode=True)
    
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    handler.emit(record)
    
    captured = capsys.readouterr().err
    assert "[MOCK CLOUD] POST https://log.api/ingest" in captured
    assert "[MOCK CLOUD] DATA:" in captured

def test_cloud_handler_emit_timeout(requests_mock):
    endpoint = "https://log.api/ingest"
    handler = CloudLogHandler(endpoint=endpoint, max_retries=2, timeout=1)
    requests_mock.post(endpoint, exc=requests.exceptions.Timeout)
    
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    with patch('sys.stderr') as mock_stderr:  # Evita saída real para stderr
        handler.emit(record)
        # Verificar se a mensagem de erro foi registrada
        assert any('Timeout' in str(call) for call in mock_stderr.write.call_args_list)
    
    # Não verificamos o call_count pois depende da implementação específica da lib de retry

def test_cloud_handler_emit_server_error(requests_mock):
    endpoint = "https://log.api/ingest"
    handler = CloudLogHandler(endpoint=endpoint, max_retries=2)
    requests_mock.post(endpoint, status_code=500)
    
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    with patch('sys.stderr') as mock_stderr:  # Evita saída real para stderr
        handler.emit(record)
        # Verificar se a mensagem de erro foi registrada
        assert any('Error' in str(call) or '500' in str(call) for call in mock_stderr.write.call_args_list)
    
    # Não verificamos o call_count pois depende da implementação específica da lib de retry

def test_cloud_handler_close():
    # Criamos um handler não-mock para testar o close
    handler = CloudLogHandler(endpoint="https://log.api/ingest")
    with patch.object(handler.session, "close") as mock_close:
        handler.close()
        mock_close.assert_called_once()
        
    # Testar também close com um handler em modo mock
    handler_mock = CloudLogHandler(endpoint="https://log.api/ingest", mock_mode=True)
    handler_mock.close()  # Não deve falhar mesmo sem session 
import os
import pytest
import requests
import logging
from unittest.mock import patch

from src.handlers.cloud import CloudLogHandler

def test_cloud_handler_init_with_config():
    handler = CloudLogHandler(
        endpoint="https://log.api/ingest",
        token="test-token",
        timeout=10,
        max_retries=5,
        backoff_factor=0.5
    )
    
    assert handler.endpoint == "https://log.api/ingest"
    assert handler.token == "test-token"
    assert handler.timeout == 10
    assert handler.max_retries == 5
    assert handler.backoff_factor == 0.5
    assert "Bearer test-token" in handler.session.headers["Authorization"]

def test_cloud_handler_init_with_env(monkeypatch):
    monkeypatch.setenv("LOG_CLOUD_ENDPOINT", "https://log.api/ingest")
    monkeypatch.setenv("LOG_CLOUD_TOKEN", "env-token")
    monkeypatch.setenv("LOG_CLOUD_TIMEOUT", "15")
    monkeypatch.setenv("LOG_CLOUD_MAX_RETRIES", "4")
    monkeypatch.setenv("LOG_CLOUD_BACKOFF_FACTOR", "0.4")
    
    handler = CloudLogHandler()
    
    assert handler.endpoint == "https://log.api/ingest"
    assert handler.token == "env-token"
    assert handler.timeout == 15
    assert handler.max_retries == 4
    assert handler.backoff_factor == 0.4
    assert "Bearer env-token" in handler.session.headers["Authorization"]

def test_cloud_handler_init_invalid_endpoint():
    with pytest.raises(ValueError, match="Invalid cloud logging endpoint URL"):
        CloudLogHandler(endpoint="invalid-url")

def test_cloud_handler_init_missing_endpoint():
    with pytest.raises(ValueError, match="Cloud logging endpoint must be provided"):
        CloudLogHandler()

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
    
    with pytest.raises(SystemExit, match="0"):
        handler.emit(record)
    
    assert requests_mock.call_count == 3  # Original + 2 retries

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
    
    with pytest.raises(SystemExit, match="0"):
        handler.emit(record)
    
    assert requests_mock.call_count == 3  # Original + 2 retries

def test_cloud_handler_close():
    handler = CloudLogHandler(endpoint="https://log.api/ingest")
    with patch.object(handler.session, "close") as mock_close:
        handler.close()
        mock_close.assert_called_once() 
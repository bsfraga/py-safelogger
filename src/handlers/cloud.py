import logging
import sys
import os
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class CloudLogHandler(logging.Handler):
    """
    Handler para envio de logs para um endpoint HTTP com suporte a retry, timeout e validações.
    
    Configuração via argumentos:
        configure_logging(
            handlers=["console", "cloud"], 
            cloud_handler_config={
                "endpoint": "https://log.api/ingest",
                "token": "abc123",
                "timeout": 5,
                "max_retries": 3,
                "backoff_factor": 0.3
            }
        )
    
    Configuração via variáveis de ambiente:
        LOG_CLOUD_ENDPOINT=https://log.api/ingest
        LOG_CLOUD_TOKEN=abc123
        LOG_CLOUD_TIMEOUT=5
        LOG_CLOUD_MAX_RETRIES=3
        LOG_CLOUD_BACKOFF_FACTOR=0.3
    """
    
    def __init__(
        self, 
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        backoff_factor: Optional[float] = None,
        **kwargs
    ):
        super().__init__()
        
        # Configuração via env ou parâmetros
        self.endpoint = endpoint or os.getenv("LOG_CLOUD_ENDPOINT")
        self.token = token or os.getenv("LOG_CLOUD_TOKEN")
        self.timeout = int(timeout or os.getenv("LOG_CLOUD_TIMEOUT", "5"))
        self.max_retries = int(max_retries or os.getenv("LOG_CLOUD_MAX_RETRIES", "3"))
        self.backoff_factor = float(backoff_factor or os.getenv("LOG_CLOUD_BACKOFF_FACTOR", "0.3"))
        
        # Validação do endpoint
        if not self.endpoint:
            raise ValueError("Cloud logging endpoint must be provided via config or LOG_CLOUD_ENDPOINT")
        
        try:
            parsed = urlparse(self.endpoint)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError
        except ValueError:
            raise ValueError(f"Invalid cloud logging endpoint URL: {self.endpoint}")
            
        # Configuração da sessão HTTP com retry
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=[408, 429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Envia o log para o endpoint configurado com retry e tratamento de erros.
        """
        if not self.endpoint:
            self.handleError(record)
            return
            
        try:
            log_entry = self.format(record)
            headers = {"Content-Type": "application/json"}
            
            response = self.session.post(
                self.endpoint,
                json={"message": log_entry},
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
        except requests.exceptions.Timeout:
            self.handleError(record)
            print(f"[CLOUD LOG] Timeout sending log to {self.endpoint}", file=sys.stderr)
            
        except requests.exceptions.RequestException as e:
            self.handleError(record)
            print(f"[CLOUD LOG] Error sending log to {self.endpoint}: {str(e)}", file=sys.stderr)
            
        except Exception as e:
            self.handleError(record)
            print(f"[CLOUD LOG] Unexpected error: {str(e)}", file=sys.stderr)
    
    def close(self) -> None:
        """
        Fecha a sessão HTTP ao finalizar o handler.
        """
        if hasattr(self, "session"):
            self.session.close()
        super().close() 
import logging
import sys

class CloudLogHandler(logging.Handler):
    """
    Handler mock para envio de logs para um endpoint HTTP (simulado).
    Exemplo de uso:
        configure_logging(handlers=["console", "cloud"], cloud_handler_config={"endpoint": "https://mock.log/api", "token": "abc"})
    """
    def __init__(self, endpoint: str, token: str = None, **kwargs):
        super().__init__()
        self.endpoint = endpoint
        self.token = token
    def emit(self, record):
        log_entry = self.format(record)
        print(f"[MOCK CLOUD] POST {self.endpoint} - Token: {self.token} - Payload: {log_entry}", file=sys.stderr)
        # Aqui seria feito o requests.post(self.endpoint, ...) 
import logging
import logging.config
import os
import json
from typing import Optional, Dict, Any, List

try:
    import yaml
except ImportError:
    yaml = None

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

class RedactFilter(logging.Filter):
    """
    Filtro para redação de campos sensíveis em registros de log.
    Exemplo de uso:
        configure_logging(redact_fields=["password", "token"])
    """
    def __init__(self, fields: List[str]):
        super().__init__()
        self.fields = set(fields)
    def filter(self, record):
        for field in self.fields:
            if hasattr(record, field):
                setattr(record, field, "[REDACTED]")
            # Se o campo estiver no dicionário extra/contexto
            if hasattr(record, "__dict__") and field in record.__dict__:
                record.__dict__[field] = "[REDACTED]"
        return True


def configure_logging(
    env: str = None,
    log_format: str = None,
    log_level: str = None,
    log_file: Optional[str] = None,
    rotation: Optional[Dict[str, Any]] = None,
    redact_fields: Optional[List[str]] = None,
    handlers: Optional[List[str]] = None,
    config_dict: Optional[Dict[str, Any]] = None,
    config_file: Optional[str] = None,
    use_structlog: bool = False,
    structlog_context: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """
    Configura o sistema de logging de forma centralizada e estruturada.
    Prioridade: config_dict > config_file > parâmetros/variáveis de ambiente.

    Exemplos de uso:
    >>> configure_logging(redact_fields=["password", "token"])
    >>> logger.info("Cadastro", extra={"email": "user@exemplo.com", "password": "senha123"})
    # Saída: ... "password": "[REDACTED]"
    """
    config = None
    if config_dict:
        config = config_dict
    elif config_file:
        ext = os.path.splitext(config_file)[-1].lower()
        with open(config_file, 'r', encoding='utf-8') as f:
            if ext in ['.yaml', '.yml'] and yaml:
                config = yaml.safe_load(f)
            elif ext == '.json':
                config = json.load(f)
            else:
                raise ValueError(f"Formato de arquivo não suportado: {config_file}")
    
    if not config:
        env = env or os.getenv("LOG_ENV", "production")
        log_format = log_format or os.getenv("LOG_FORMAT", "json")
        log_level = log_level or os.getenv("LOG_LEVEL", "INFO")
        log_file = log_file or os.getenv("LOG_FILE")
        handlers = handlers or ["console"]
        
        formatter = {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s"
        }
        if log_format == "json":
            try:
                from pythonjsonlogger import jsonlogger
                formatter = {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s"
                }
            except ImportError:
                pass
        
        handler_defs = {}
        if "console" in handlers:
            handler_defs["console"] = {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "default"
            }
        if "file" in handlers and log_file:
            file_handler = {
                "level": log_level,
                "formatter": "default",
                "filename": log_file,
                "encoding": "utf-8"
            }
            # Rotação por tamanho (RotatingFileHandler)
            if rotation and rotation.get("type", "size") == "size":
                file_handler["class"] = "logging.handlers.RotatingFileHandler"
                file_handler["maxBytes"] = rotation.get("maxBytes", 10*1024*1024)
                file_handler["backupCount"] = rotation.get("backupCount", 7)
            # Rotação por tempo (TimedRotatingFileHandler)
            elif rotation and rotation.get("type") == "time":
                file_handler["class"] = "logging.handlers.TimedRotatingFileHandler"
                file_handler["when"] = rotation.get("when", "midnight")
                file_handler["interval"] = rotation.get("interval", 1)
                file_handler["backupCount"] = rotation.get("backupCount", 7)
                file_handler["utc"] = rotation.get("utc", True)
            # Sem rotação (default: RotatingFileHandler com maxBytes alto)
            else:
                file_handler["class"] = "logging.handlers.RotatingFileHandler"
                file_handler["maxBytes"] = 0
                file_handler["backupCount"] = 1
            handler_defs["file"] = file_handler
        # Adicionar outros handlers customizados (ex: cloud) conforme necessário
        
        filters = {}
        if redact_fields:
            filters["redact"] = {
                "()": RedactFilter,
                "fields": redact_fields
            }
        
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": formatter
            },
            "handlers": handler_defs,
            "filters": filters,
            "root": {
                "level": log_level,
                "handlers": list(handler_defs.keys())
            }
        }
        if filters:
            for h in handler_defs:
                config["handlers"][h]["filters"] = list(filters.keys())
    
    logging.config.dictConfig(config)

    # Configuração do structlog para logging estruturado/contextual
    if use_structlog and STRUCTLOG_AVAILABLE:
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.CallsiteParameterAdder({
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }),
            structlog.processors.JSONRenderer() if log_format == "json" else structlog.dev.ConsoleRenderer(),
        ]
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        if structlog_context:
            logger = structlog.get_logger()
            logger = logger.bind(**structlog_context)
            return logger
    else:
        # Logging tradicional
        return logging.getLogger()


def get_structlog_logger(**context):
    """
    Retorna um logger structlog com contexto já vinculado (se structlog estiver disponível).
    Caso contrário, retorna o logger tradicional do logging.
    """
    if STRUCTLOG_AVAILABLE:
        logger = structlog.get_logger()
        if context:
            logger = logger.bind(**context)
        return logger
    else:
        return logging.getLogger()


def get_traditional_logger():
    """
    Retorna o logger tradicional do logging.
    """
    return logging.getLogger() 
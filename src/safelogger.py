import logging
import logging.config
from typing import Optional, Dict, Any, List

from src.filters.redact import RedactFilter
from src.handlers.cloud import CloudLogHandler
from src.utils.config import load_config_dict, load_config_file, load_config_from_env
from src.structlog_support import configure_structlog

__all__ = [
    "configure_logging",
    "get_structlog_logger",
    "get_traditional_logger",
    "RedactFilter",
    "CloudLogHandler"
]

"""
Lib de Logging Python — API Pública

Exemplos de uso:

# 1. Configuração básica
from py_safelogger import configure_logging, get_traditional_logger
configure_logging(log_level="INFO")
logger = get_traditional_logger()
logger.info("Mensagem informativa", extra={"user_id": 123})

# 2. Logging estruturado com contexto (structlog)
from py_safelogger import configure_logging, get_structlog_logger
configure_logging(use_structlog=True)
logger = get_structlog_logger(user_id=42, role="admin")
logger.info("Usuário autenticado")

# 3. Logging de erros com stacktrace
try:
    1/0
except Exception:
    logger.exception("Erro de divisão")

# 4. Logging com redação de dados sensíveis
configure_logging(redact_fields=["password"])
logger.info("Cadastro", extra={"email": "user@exemplo.com", "password": "senha123"})
# Saída: ... "password": "[REDACTED]"

# 5. Logging com handler cloud (mock)
configure_logging(handlers=["console", "cloud"], cloud_handler_config={"endpoint": "https://mock.log/api", "token": "abc"})
logger.info("Evento enviado para a nuvem", extra={"event": "login"})
"""


try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


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
    cloud_handler_config: Optional[Dict[str, Any]] = None,
    custom_handlers: Optional[Dict[str, Any]] = None,
    use_structlog: bool = False,
    structlog_context: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """
    Configura o sistema de logging de forma centralizada e estruturada.
    Prioridade: config_dict > config_file > parâmetros/variáveis de ambiente.

    Exemplos de uso:
    >>> configure_logging(handlers=["console", "cloud"], cloud_handler_config={"endpoint": "https://mock.log/api", "token": "abc"})
    >>> configure_logging(custom_handlers={"myhandler": {"class": "my.module.MyHandler", ...}})
    """
    # 1. Carregar configuração
    config = load_config_dict(config_dict) or load_config_file(config_file)
    if not config:
        envs = load_config_from_env()
        env = env or envs["env"]
        log_format = log_format or envs["log_format"]
        log_level = log_level or envs["log_level"]
        log_file = log_file or envs["log_file"]
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
            if rotation and rotation.get("type", "size") == "size":
                file_handler["class"] = "logging.handlers.RotatingFileHandler"
                file_handler["maxBytes"] = rotation.get("maxBytes", 10*1024*1024)
                file_handler["backupCount"] = rotation.get("backupCount", 7)
            elif rotation and rotation.get("type") == "time":
                file_handler["class"] = "logging.handlers.TimedRotatingFileHandler"
                file_handler["when"] = rotation.get("when", "midnight")
                file_handler["interval"] = rotation.get("interval", 1)
                file_handler["backupCount"] = rotation.get("backupCount", 7)
                file_handler["utc"] = rotation.get("utc", True)
            else:
                file_handler["class"] = "logging.handlers.RotatingFileHandler"
                file_handler["maxBytes"] = 0
                file_handler["backupCount"] = 1
            handler_defs["file"] = file_handler
        if "cloud" in handlers and cloud_handler_config:
            handler_defs["cloud"] = {
                "()": CloudLogHandler,
                **cloud_handler_config,
                "level": log_level,
                "formatter": "default"
            }
        # Permitir extensão via custom_handlers
        if custom_handlers:
            for name, hcfg in custom_handlers.items():
                handler_defs[name] = hcfg
        
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
        return configure_structlog(processors, log_format, structlog_context)
    else:
        # Logging tradicional
        return logging.getLogger()


def get_structlog_logger(**context):
    """
    Retorna um logger structlog com contexto já vinculado (se structlog estiver disponível).
    Caso contrário, retorna o logger tradicional do logging.
    """
    if STRUCTLOG_AVAILABLE:
        import structlog
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
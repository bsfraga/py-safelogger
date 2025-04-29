import logging
import logging.config
import os
import json
from typing import Optional, Dict, Any, List

try:
    import yaml
except ImportError:
    yaml = None


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
    **kwargs
):
    """
    Configura o sistema de logging de forma centralizada.
    Prioridade: config_dict > config_file > parâmetros/variáveis de ambiente.

    Exemplos de uso:
    >>> configure_logging(log_level="DEBUG", log_format="json", log_file="app.log")
    >>> configure_logging(config_file="logging.yaml")
    >>> configure_logging(config_dict={...})
    """
    # 1. Carregar configuração de dicionário, arquivo ou parâmetros
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
    
    # 2. Se não houver config pronta, montar a partir dos parâmetros/env
    if not config:
        # Permitir sobrescrita por variáveis de ambiente
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
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "default",
                "filename": log_file,
                "encoding": "utf-8",
                "backupCount": 7,
                "maxBytes": 10*1024*1024
            }
            if rotation:
                file_handler.update(rotation)
            handler_defs["file"] = file_handler
        # Adicionar outros handlers customizados (ex: cloud) conforme necessário
        
        # Filtro para redação de campos sensíveis
        filters = {}
        if redact_fields:
            class RedactFilter(logging.Filter):
                def filter(self, record):
                    for field in redact_fields:
                        if hasattr(record, field):
                            setattr(record, field, "[REDACTED]")
                    return True
            filters["redact"] = {
                "()": RedactFilter
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
    
    # 3. Aplicar configuração
    logging.config.dictConfig(config)
    
    # Exemplo básico de configuração inicial
    logging.basicConfig(level=log_level)
    
    # Placeholder para futuras implementações
    pass 
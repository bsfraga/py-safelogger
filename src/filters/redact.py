import logging
from typing import List, Any
import json

class RedactFilter(logging.Filter):
    """
    Filtro recursivo para redação de campos sensíveis em registros de log.
    Redige campos em dicts, listas e strings JSON.
    Exemplo de uso:
        configure_logging(redact_fields=["password", "token"])
    """
    def __init__(self, fields: List[str]):
        super().__init__()
        self.fields = set(fields)

    def redact_recursive(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: ("[REDACTED]" if k in self.fields else self.redact_recursive(v)) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.redact_recursive(i) for i in obj]
        elif isinstance(obj, str):
            # Tenta redigir se for um JSON serializado
            try:
                parsed = json.loads(obj)
                redacted = self.redact_recursive(parsed)
                return json.dumps(redacted)
            except Exception:
                return obj
        return obj

    def filter(self, record):
        # Redige atributos do record
        if hasattr(record, "__dict__"):
            for field in self.fields:
                if field in record.__dict__:
                    record.__dict__[field] = "[REDACTED]"
            # Redige recursivamente extras
            if hasattr(record, "args") and isinstance(record.args, dict):
                record.args = self.redact_recursive(record.args)
            if hasattr(record, "extra") and isinstance(record.extra, dict):
                record.extra = self.redact_recursive(record.extra)
        return True 
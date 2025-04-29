import os
import json
from typing import Optional, Dict, Any

try:
    import yaml
except ImportError:
    yaml = None

def load_config_dict(config_dict: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    return config_dict if config_dict else None

def load_config_file(config_file: Optional[str]) -> Optional[Dict[str, Any]]:
    if not config_file:
        return None
    ext = os.path.splitext(config_file)[-1].lower()
    with open(config_file, 'r', encoding='utf-8') as f:
        if ext in ['.yaml', '.yml'] and yaml:
            return yaml.safe_load(f)
        elif ext == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Formato de arquivo não suportado: {config_file}")

def load_config_from_env() -> Dict[str, Any]:
    return {
        "env": os.getenv("LOG_ENV", "production"),
        "log_format": os.getenv("LOG_FORMAT", "json"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "log_file": os.getenv("LOG_FILE"),
    } 
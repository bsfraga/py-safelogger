import os
import json
from typing import Optional, Dict, Any, Union

try:
    import yaml
except ImportError:
    yaml = None

class MissingEnvError(Exception):
    """Exceção lançada quando uma variável de ambiente obrigatória está ausente."""
    def __init__(self, var_name: str):
        self.var_name = var_name
        super().__init__(f"Variável de ambiente obrigatória não encontrada: {var_name}")

def get_env_var(
    var_name: str,
    required: bool = True,
    default: Any = None,
    var_type: type = str
) -> Optional[Any]:
    """
    Obtém uma variável de ambiente com validação.
    
    Args:
        var_name: Nome da variável de ambiente
        required: Se True, lança MissingEnvError se a variável não existir
        default: Valor padrão caso a variável não exista e required=False
        var_type: Tipo esperado da variável (str, int, float, bool)
    
    Returns:
        Valor da variável de ambiente convertido para o tipo especificado
    
    Raises:
        MissingEnvError: Se a variável for obrigatória e não existir
        ValueError: Se o valor não puder ser convertido para o tipo especificado
    """
    value = os.getenv(var_name)
    
    if value is None:
        if required:
            raise MissingEnvError(var_name)
        return default
    
    try:
        if var_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        return var_type(value)
    except ValueError:
        raise ValueError(f"Não foi possível converter '{value}' para {var_type.__name__} na variável {var_name}")

def load_config_dict(config_dict: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Carrega configuração a partir de um dicionário."""
    return config_dict if config_dict else None

def load_config_file(config_file: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Carrega configuração a partir de um arquivo YAML ou JSON.
    
    Args:
        config_file: Caminho para o arquivo de configuração
    
    Returns:
        Dicionário com as configurações ou None se o arquivo não for fornecido
    
    Raises:
        ValueError: Se o formato do arquivo não for suportado
        FileNotFoundError: Se o arquivo não existir
    """
    if not config_file:
        return None
        
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_file}")
        
    ext = os.path.splitext(config_file)[-1].lower()
    with open(config_file, 'r', encoding='utf-8') as f:
        if ext in ['.yaml', '.yml'] and yaml:
            return yaml.safe_load(f)
        elif ext == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Formato de arquivo não suportado: {config_file}")

def load_config_from_env() -> Dict[str, Any]:
    """
    Carrega configuração a partir de variáveis de ambiente com validação.
    
    Variáveis obrigatórias:
    - LOG_LEVEL: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Variáveis opcionais:
    - LOG_ENV: Ambiente (default: production)
    - LOG_FORMAT: Formato do log (default: json)
    - LOG_FILE: Arquivo de log
    - LOG_HTTP_URL: URL para envio de logs via HTTP
    
    Returns:
        Dicionário com as configurações carregadas
        
    Raises:
        MissingEnvError: Se alguma variável obrigatória estiver ausente
        ValueError: Se algum valor não puder ser convertido para o tipo esperado
    """
    # Validar LOG_LEVEL (obrigatório)
    log_level = get_env_var(
        "LOG_LEVEL",
        required=True,
        default="INFO"
    ).upper()
    
    if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        raise ValueError(f"Nível de log inválido: {log_level}")
    
    # Carregar outras configurações
    config = {
        "env": get_env_var("LOG_ENV", required=False, default="production"),
        "log_format": get_env_var("LOG_FORMAT", required=False, default="json"),
        "log_level": log_level,
        "log_file": get_env_var("LOG_FILE", required=False),
    }
    
    # Configurações HTTP (se fornecidas)
    http_url = get_env_var("LOG_HTTP_URL", required=False)
    if http_url:
        config["http"] = {
            "url": http_url,
            "timeout": get_env_var("LOG_HTTP_TIMEOUT", required=False, default=5, var_type=int),
            "max_retries": get_env_var("LOG_HTTP_MAX_RETRIES", required=False, default=3, var_type=int),
            "backoff_factor": get_env_var("LOG_HTTP_BACKOFF_FACTOR", required=False, default=0.3, var_type=float),
        }
    
    return config 
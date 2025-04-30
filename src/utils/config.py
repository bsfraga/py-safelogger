import os
import json
import re
import logging
from typing import Optional, Dict, Any, Union, Callable, List, Type

try:
    import yaml
except ImportError:
    yaml = None

class ConfigError(Exception):
    """Exceção base para erros de configuração."""
    pass

class MissingEnvError(ConfigError):
    """Exceção lançada quando uma variável de ambiente obrigatória está ausente."""
    def __init__(self, var_name: str):
        self.var_name = var_name
        super().__init__(f"Variável de ambiente obrigatória não encontrada: {var_name}")

class InvalidEnvError(ConfigError):
    """Exceção lançada quando uma variável de ambiente tem valor inválido."""
    def __init__(self, var_name: str, value: str, reason: str):
        self.var_name = var_name
        self.value = value
        self.reason = reason
        super().__init__(f"Valor inválido '{value}' para variável {var_name}: {reason}")

def validate_required_envs(required_keys: List[str]) -> None:
    """
    Valida se todas as variáveis de ambiente obrigatórias estão definidas.
    
    Args:
        required_keys: Lista de nomes das variáveis de ambiente obrigatórias
    
    Raises:
        EnvironmentError: Se uma ou mais variáveis de ambiente obrigatórias não estiverem definidas
    """
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        raise EnvironmentError(
            f"Variáveis de ambiente obrigatórias não encontradas: {', '.join(missing_keys)}"
        )

def get_env(key: str, default: Any = None, cast: Callable = str) -> Any:
    """
    Obtém uma variável de ambiente com type-casting seguro.
    
    Args:
        key: Nome da variável de ambiente
        default: Valor padrão caso a variável não exista
        cast: Função para converter o valor para o tipo desejado (str, int, float, bool)
    
    Returns:
        Valor da variável de ambiente convertido para o tipo especificado
    
    Raises:
        ValueError: Se o valor não puder ser convertido para o tipo especificado
    """
    value = os.getenv(key)
    
    if value is None:
        return default
    
    # Tratamento especial para valores booleanos
    if cast == bool:
        return value.lower() in ('true', '1', 'yes', 'on', 'y', 'sim', 's')
    
    try:
        return cast(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Não foi possível converter o valor '{value}' da variável '{key}' para {cast.__name__}: {str(e)}")

def validate_log_level(level: str) -> None:
    """
    Valida se o nível de log é válido.
    
    Args:
        level: Nível de log a ser validado
        
    Raises:
        ValueError: Se o nível de log for inválido
    """
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if level.upper() not in valid_levels:
        raise ValueError(f"Nível de log inválido: {level}. Deve ser um dos: {', '.join(valid_levels)}")

def validate_url(url: str) -> None:
    """
    Valida se a URL está em formato válido.
    
    Args:
        url: URL a ser validada
        
    Raises:
        ValueError: Se a URL for inválida
    """
    url_pattern = re.compile(
        r'^(http|https)://'  # http:// ou https://
        r'('
        r'([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+'  # domínio com pontos
        r'[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?'  # TLD
        r'|'
        r'localhost'  # localhost
        r')'
        r'(:\d+)?'  # porta (opcional)
        r'(/[a-zA-Z0-9_\.-]*)*'  # caminho (opcional)
        r'(\?([a-zA-Z0-9_\.-]+=[a-zA-Z0-9_\.-]+)(&[a-zA-Z0-9_\.-]+=[a-zA-Z0-9_\.-]+)*)?$'  # query params (opcional)
    )
    
    if not url_pattern.match(url):
        raise ValueError(f"URL inválida: {url}")

def get_env_var(
    var_name: str,
    required: bool = True,
    default: Any = None,
    var_type: type = str,
    validator: Optional[Callable[[str], None]] = None
) -> Optional[Any]:
    """
    Obtém uma variável de ambiente com validação.
    
    Args:
        var_name: Nome da variável de ambiente
        required: Se True, lança MissingEnvError se a variável não existir
        default: Valor padrão caso a variável não exista e required=False
        var_type: Tipo esperado da variável (str, int, float, bool)
        validator: Função opcional de validação adicional
    
    Returns:
        Valor da variável de ambiente convertido para o tipo especificado
    
    Raises:
        MissingEnvError: Se a variável for obrigatória e não existir
        InvalidEnvError: Se o valor não for válido
    """
    value = os.getenv(var_name)
    
    if value is None:
        if required:
            raise MissingEnvError(var_name)
        return default
    
    try:
        if var_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        typed_value = var_type(value)
        
        # Aplicar validação adicional, se fornecida
        if validator:
            try:
                validator(value)
            except ValueError as e:
                raise InvalidEnvError(var_name, value, str(e))
                
        return typed_value
    except ValueError:
        raise InvalidEnvError(
            var_name, 
            value, 
            f"Não foi possível converter para {var_type.__name__}"
        )

def load_config_dict(config_dict: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Carrega configuração a partir de um dicionário."""
    if config_dict is None:
        return None
    return config_dict

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

def load_env(require_log_level: bool = False, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Carrega configuração a partir de variáveis de ambiente com validação, 
    com chamada explícita e log de carregamento.
    
    Args:
        require_log_level: Se True, exige que LOG_LEVEL esteja definido, caso contrário usa default
        logger: Logger opcional para registrar o carregamento da configuração
    
    Variáveis obrigatórias (se require_log_level=True):
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
        InvalidEnvError: Se algum valor não puder ser convertido para o tipo esperado
    """
    if logger:
        logger.info("Iniciando carregamento de configurações a partir de variáveis de ambiente")
    
    # Usar um valor padrão se LOG_LEVEL não estiver definido (para os testes)
    value = os.getenv("LOG_LEVEL")
    if value is None:
        if require_log_level:
            raise MissingEnvError("LOG_LEVEL")
        log_level = "INFO"  # Usar default para testes
        if logger:
            logger.warning("LOG_LEVEL não encontrado, usando valor padrão: INFO")
    else:
        try:
            log_level = value.upper()
            validate_log_level(log_level)
        except ValueError as e:
            if logger:
                logger.error(f"LOG_LEVEL inválido: {e}")
            raise InvalidEnvError("LOG_LEVEL", value, str(e))
    
    # Carregar outras configurações
    config = {
        "env": get_env_var("LOG_ENV", required=False, default="production"),
        "log_format": get_env_var("LOG_FORMAT", required=False, default="json"),
        "log_level": log_level,
        "log_file": get_env_var("LOG_FILE", required=False)  # Sempre incluir log_file, mesmo que None
    }
    
    # Configurações HTTP (opcional)
    http_url = get_env_var("LOG_HTTP_URL", required=False)
    if http_url:
        try:
            validate_url(http_url)
            config["log_http_url"] = http_url
        except ValueError as e:
            if logger:
                logger.error(f"LOG_HTTP_URL inválido: {e}")
            raise InvalidEnvError("LOG_HTTP_URL", http_url, str(e))
    
    if logger:
        logger.info(f"Configurações carregadas com sucesso: {config}")
    
    return config

# Manter compatibilidade com código existente
load_config_from_env = load_env 
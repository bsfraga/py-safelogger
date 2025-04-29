# py-safelogger

Biblioteca de logging estruturado, flexível e extensível para Python, oferecendo uma solução simplificada para configuração e integração de logs em projetos de todos os tamanhos.

## Instalação

```bash
pip install py-safelogger
```

## Estrutura do Projeto

A biblioteca está organizada de forma modular para facilitar a manutenção e extensão:

```
py-safelogger/
├── src/
│   ├── filters/           # Filtros para manipulação de logs
│   │   └── redact.py      # Filtro para redação de dados sensíveis
│   ├── handlers/          # Manipuladores de destino para logs
│   │   └── cloud.py       # Handler para envio de logs para endpoints HTTP
│   ├── utils/             # Funções utilitárias
│   │   └── config.py      # Utilitários para carregamento de configurações
│   ├── structlog_support.py # Integração com structlog
│   └── safelogger.py     # Módulo principal e API pública
└── tests/
    └── test_safelogger.py # Testes unitários e integração
```

## API Pública

A biblioteca expõe as seguintes funções e classes principais:

- `configure_logging()`: Configura o sistema de logging
- `get_traditional_logger()`: Retorna um logger tradicional do Python
- `get_structlog_logger()`: Retorna um logger structlog (se disponível)
- `RedactFilter`: Filtro para redação de campos sensíveis
- `CloudLogHandler`: Handler para envio de logs para endpoints HTTP (mock)

## Exemplos de Uso

### 1. Configuração básica
```python
from py-safelogger import configure_logging, get_traditional_logger
configure_logging(log_level="INFO")
logger = get_traditional_logger()
logger.info("Mensagem informativa", extra={"user_id": 123})
```

### 2. Logging estruturado com contexto (structlog)
```python
from py-safelogger import configure_logging, get_structlog_logger
configure_logging(use_structlog=True)
logger = get_structlog_logger(user_id=42, role="admin")
logger.info("Usuário autenticado")
```

### 3. Logging de erros com stacktrace
```python
try:
    1/0
except Exception:
    logger.exception("Erro de divisão")
```

### 4. Logging com redação de dados sensíveis (recursivo)
```python
configure_logging(redact_fields=["password", "token"])
logger.info("Cadastro", extra={
    "email": "user@exemplo.com", 
    "password": "senha123", 
    "profile": {"password": "outra"}
})
# Saída: ... "password": "[REDACTED]" em todos os níveis
```

### 5. Logging com handler cloud (mock)
```python
configure_logging(
    handlers=["console", "cloud"], 
    cloud_handler_config={"endpoint": "https://mock.log/api", "token": "abc"}
)
logger.info("Evento enviado para a nuvem", extra={"event": "login"})
```

### 6. Rotação de arquivos
```python
# Rotação por tamanho
configure_logging(
    log_file="app.log", 
    rotation={"type": "size", "maxBytes": 1048576, "backupCount": 5}
)

# Rotação por tempo
configure_logging(
    log_file="app.log", 
    rotation={"type": "time", "when": "midnight", "interval": 1, "backupCount": 7}
)
```

### 7. Configuração via arquivo ou dicionário
```python
# Via arquivo YAML
configure_logging(config_file="logging_config.yaml")

# Via dicionário
config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"default": {"format": "%(asctime)s %(levelname)s %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
    "root": {"level": "INFO", "handlers": ["console"]}
}
configure_logging(config_dict=config)
```

### 8. Configuração via variáveis de ambiente
```
# Defina as variáveis de ambiente
export LOG_ENV=production
export LOG_FORMAT=json
export LOG_LEVEL=WARNING
export LOG_FILE=/var/log/app.log

# No código, não precisa passar parâmetros
from py-safelogger import configure_logging
configure_logging()  # Carrega configuração das variáveis de ambiente
```

## Segurança e Privacidade
- O filtro de redação é recursivo e cobre campos sensíveis em estruturas aninhadas e JSON serializado
- Para ambientes críticos (compliance, auditoria): recomenda-se integrar com soluções de logs imutáveis
- A arquitetura permite integração com handlers externos para necessidades específicas de segurança

## Cenários Indicados
- Projetos de médio e grande porte que exigem:
  - Padronização de logging
  - Logging estruturado (JSON)
  - Proteção de dados sensíveis
  - Integração com sistemas de observabilidade
  - Rotação e múltiplos destinos de log
  - Extensibilidade via handlers e filtros customizados

## Cenários Não Indicados
- Scripts simples ou automações pequenas onde o logging padrão do Python já é suficiente
- Ambientes que exigem logs imutáveis nativamente (sem integração com storage externo)
- Projetos onde a simplicidade e o footprint mínimo são prioridade absoluta

## Desenvolvimento e CI/CD

A biblioteca inclui uma pipeline GitHub Actions para automação de testes e publicação:
- Execução de testes unitários e de integração
- Relatório de cobertura de código (cobertura atual: 88%)
- Build e publicação automática no PyPI quando uma nova tag é criada

## Licença

MIT 
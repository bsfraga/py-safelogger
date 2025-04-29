# Lib de Logging Python — Projeto para PyPI

## Visão Geral

Esta biblioteca tem como objetivo fornecer uma solução padronizada, fácil de integrar e extensível para logging estruturado em projetos Python, reduzindo redundância de código e garantindo integridade e observabilidade.

## Requisitos e Escopo

- Configuração centralizada e flexível via função utilitária ou arquivo externo
- Suporte a logging estruturado (JSON) e logs tradicionais
- Rotação de arquivos de log (por tamanho e/ou tempo)
- Proteção de dados sensíveis (filtros/redação customizáveis)
- Integração fácil com handlers externos (stdout, arquivos, cloud, etc.)
- Uso de loggers por módulo, seguindo o padrão `logging.getLogger(__name__)`
- Compatibilidade com padrões do Python logging, structlog e python-json-logger
- Facilidade de uso e integração em projetos existentes
- Suporte a ambientes distintos (dev, prod, test)

## Padrões de Implementação

### 1. Configuração Centralizada

A configuração deve ser feita por uma função utilitária, por exemplo `configure_logging`, que aceita parâmetros para ambiente, formato, handlers e filtros.

**Exemplo:**
```python
from lib_logging import configure_logging

configure_logging(
    env="production",
    log_format="json",
    log_level="INFO",
    log_file="/var/log/app.log",
    rotation={"when": "midnight", "backupCount": 7},
    redact_fields=["password", "credit_card"]
)
```

- Recomenda-se o uso de `logging.config.dictConfig` para flexibilidade.
- Permitir configuração via dicionário, arquivo YAML/JSON ou variáveis de ambiente.

### 2. Logging Estruturado

A biblioteca deve suportar logs em formato JSON, facilitando integração com sistemas de observabilidade (ELK, Datadog, etc.).

**Exemplo:**
```python
logger.info("Usuário autenticado", extra={"user_id": 42, "role": "admin"})
```

**Saída esperada (JSON):**
```json
{
  "timestamp": "2024-06-01T12:00:00Z",
  "level": "INFO",
  "message": "Usuário autenticado",
  "user_id": 42,
  "role": "admin"
}
```

- Utilizar `python-json-logger` ou `structlog` para formatação.
- Permitir campos contextuais via `extra` ou binding de contexto.

### 3. Rotação de Arquivos

A biblioteca deve expor configuração para rotação automática de arquivos de log.

**Exemplo:**
```python
rotation={"when": "midnight", "backupCount": 7}  # Rotaciona diariamente, mantém 7 arquivos
```

- Usar `RotatingFileHandler` ou `TimedRotatingFileHandler`.
- Permitir configuração de tamanho máximo e quantidade de backups.

### 4. Proteção de Dados Sensíveis

Implementar filtros para mascarar/redigir campos sensíveis nos logs.

**Exemplo:**
```python
logger.info("Cadastro de usuário", extra={"email": "user@exemplo.com", "password": "[REDACTED]"})
```

- Permitir lista de campos a serem redigidos.
- Exemplo de filtro customizado:
```python
class RedactFilter(logging.Filter):
    def __init__(self, fields):
        self.fields = set(fields)
    def filter(self, record):
        for field in self.fields:
            if hasattr(record, field):
                setattr(record, field, "[REDACTED]")
        return True
```

### 5. Integração com Handlers Externos

A biblioteca deve facilitar o envio de logs para múltiplos destinos:
- Console (stdout/stderr)
- Arquivos
- Serviços externos (ex: HTTP, cloud, syslog)

**Exemplo:**
```python
configure_logging(
    handlers=["console", "file", "cloud"],
    cloud_handler_config={"endpoint": "https://logs.exemplo.com", "token": "..."}
)
```

- Permitir extensão via handlers customizados.

## Exemplos de Uso

### Uso Básico
```python
import logging
from lib_logging import configure_logging

configure_logging(env="production")
logger = logging.getLogger(__name__)
logger.info("Mensagem informativa", extra={"user_id": 123})
```

### Logging Estruturado com Contexto
```python
logger = logging.getLogger("app.auth")
logger.info("Login realizado", extra={"user_id": 42, "ip": "1.2.3.4"})
```

### Logging de Erros com Stacktrace
```python
try:
    1/0
except Exception:
    logger.exception("Erro de divisão")
```

### Logging com Redação de Dados Sensíveis
```python
logger.info("Cadastro", extra={"email": "user@exemplo.com", "password": "senha123"})
# Saída: ... "password": "[REDACTED]"
```

## Testes e Build

- **Testes unitários:** Cobrir funções utilitárias, filtros, formatação e integração com handlers.
- **Testes de integração:** Simular cenários reais de logging em diferentes ambientes.
- **Cobertura:** Recomenda-se cobertura mínima de 90%.
- **Build:**
  - Usar `setuptools`/`poetry` para empacotamento.
  - Incluir `pyproject.toml` e `setup.cfg`.
  - Automatizar testes e build com GitHub Actions ou similar.
- **Publicação PyPI:**
  - Instruções para gerar distribuição (`python -m build`)
  - Upload seguro (`twine upload dist/*`)

## Referências e Melhores Práticas

- [Python Logging Best Practices: The Ultimate Guide](https://coralogix.com/blog/python-logging-best-practices-tips/)
- [10 Best Practices for Logging in Python | Better Stack](https://betterstack.com/community/guides/logging/python/python-logging-best-practices/)
- [structlog documentation](https://www.structlog.org/en/stable/)
- [python-json-logger](https://github.com/madzak/python-json-logger)
- [PEP 282 – A Logging System](https://peps.python.org/pep-0282/)

---

> Este documento serve como base para a implementação e evolução da biblioteca, garantindo aderência a padrões modernos e melhores práticas de logging em Python.

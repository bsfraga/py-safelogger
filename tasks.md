# Tasks para Implementação da Lib de Logging Python

## 1. Estrutura Inicial do Projeto
- [x] Criar estrutura de diretórios do projeto (src/, tests/, docs/)
- [x] Configurar pyproject.toml e setup.cfg
- [x] Definir dependências principais (logging, python-json-logger, structlog)

## 2. Configuração Centralizada
- [x] Implementar função utilitária `configure_logging`
- [x] Permitir configuração via dicionário, arquivo YAML/JSON e variáveis de ambiente
- [x] Suportar parâmetros: ambiente, formato, nível, arquivo, rotação, campos a redigir, handlers
- [x] Documentar exemplos de configuração

## 3. Logging Estruturado
- [x] Integrar suporte a logs em JSON (python-json-logger/structlog)
- [x] Permitir campos contextuais via `extra` e binding de contexto
- [x] Garantir compatibilidade com logs tradicionais

## 4. Rotação de Arquivos
- [x] Implementar suporte a RotatingFileHandler e TimedRotatingFileHandler
- [x] Permitir configuração de rotação por tamanho, tempo e quantidade de backups

## 5. Proteção de Dados Sensíveis
- [x] Implementar filtro customizável para redação de campos sensíveis
- [x] Permitir lista de campos a serem redigidos
- [x] Testar e documentar exemplos de uso

## 6. Integração com Handlers Externos
- [x] Implementar handlers para console, arquivo e cloud (mock)
- [x] Permitir extensão via handlers customizados
- [x] Documentar exemplos de integração

## 7. API Pública e Exemplos
- [x] Definir e documentar API pública da lib
- [x] Criar exemplos de uso básico, estruturado, com contexto, erros e redação

## 8. Testes
- [x] Escrever testes unitários para funções utilitárias, filtros, formatação e handlers
- [x] Escrever testes de integração para cenários reais de logging
- [x] Garantir cobertura mínima de 90%

## 9. Organizar estrutura do projeto
- [x] Organizar estrutura do projeto de forma modular a partir das classes e funções implementadas
- [x] Criar um arquivo README.md com exemplos de uso e links para a documentação detalhada

## 10. Build e Publicação
- [ ] Configurar build com setuptools/poetry
- [ ] Automatizar testes e build (GitHub Actions ou similar)
- [ ] Documentar processo de build e publicação no PyPI

## 11. Documentação e Melhores Práticas
- [ ] Escrever documentação detalhada (README, exemplos, referências)
- [ ] Incluir links para melhores práticas e referências externas

---

> Atualize o status das tasks conforme o progresso da implementação.

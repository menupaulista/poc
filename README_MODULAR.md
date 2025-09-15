# Web Scraper Modular - Doisporum.net

Este projeto foi refatorado seguindo princípios SOLID e arquitetura modular para melhor organização, manutenibilidade e testabilidade.

## 📁 Estrutura Modular

```
src/
├── __init__.py
├── config.py                 # Constantes e configurações
├── models/                   # Entidades de domínio
│   ├── __init__.py
│   └── offer.py             # Modelo OfferItem
├── protocols/               # Interfaces/Protocolos (Dependency Inversion)
│   ├── __init__.py
│   └── base.py             # HttpClient, Parser, Repository protocols
├── clients/                 # Implementações de clientes HTTP
│   ├── __init__.py
│   └── httpx_client.py     # Cliente HTTP assíncrono
├── parsers/                # Parsers específicos para diferentes páginas
│   ├── __init__.py
│   ├── list_parser.py      # Parser para páginas de lista
│   └── detail_parser.py    # Parser para páginas de detalhes
├── repositories/           # Persistência de dados
│   ├── __init__.py
│   └── pandas_repository.py # Repositório usando pandas
└── services/               # Serviços de negócio
    ├── __init__.py
    ├── link_collector.py   # Coleta de links
    ├── detail_scraper.py   # Scraping de detalhes
    └── coordinator.py      # Coordenador principal
```

## 🏗️ Arquitetura

### Princípios SOLID Aplicados

1. **Single Responsibility Principle (SRP)**: Cada classe tem uma única responsabilidade
   - `OfferItem`: Representa uma oferta
   - `AsyncHttpxClient`: Gerencia requisições HTTP
   - `DoisPorUmDetailParser`: Parse de páginas de detalhes
   - `LinkCollector`: Coleta links de páginas de lista

2. **Open/Closed Principle (OCP)**: Extensível sem modificar código existente
   - Novos parsers podem ser adicionados implementando os protocolos
   - Novos repositórios podem ser criados sem alterar o código existente

3. **Liskov Substitution Principle (LSP)**: Implementações podem ser substituídas
   - Qualquer implementação de `HttpClient` pode ser usada
   - Qualquer parser que implemente `DetailParser` é intercambiável

4. **Interface Segregation Principle (ISP)**: Interfaces específicas
   - `HttpClient` para operações HTTP
   - `DetailParser` para parsing de detalhes
   - `ListPageParser` para parsing de listas
   - `OfferRepository` para persistência

5. **Dependency Inversion Principle (DIP)**: Dependência de abstrações
   - Serviços dependem de protocolos, não de implementações concretas
   - Injeção de dependência no `main()`

### Padrões de Design

- **Strategy Pattern**: Diferentes parsers para diferentes tipos de página
- **Repository Pattern**: Abstração da camada de persistência
- **Service Layer**: Lógica de negócio separada em serviços
- **Coordinator Pattern**: Orquestração do processo completo

## 🚀 Como Usar

### Instalação

```bash
# Criar ambiente virtual
uv venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# Instalar dependências
uv add "httpx[http2]==0.28.1" beautifulsoup4 lxml pandas tqdm
```

### Execução

```bash
# Usar o scraper original (legado)
python scraper.py --seed-url "https://doisporum.net/" --max-items 120

# Usar o scraper modular
python main_modular.py --seed-url "https://doisporum.net/" --max-items 120

# Teste rápido
python test_modular.py
```

### Parâmetros

- `--seed-url`: URL inicial para scraping
- `--max-items`: Número máximo de itens (padrão: 120)
- `--rate-limit-seconds`: Tempo entre requisições (padrão: 0.8s)
- `--max-concurrency`: Requisições simultâneas (padrão: 6)
- `--csv-path`: Caminho do arquivo CSV de saída
- `--jsonl-path`: Caminho do arquivo JSONL de saída
- `--timeout`: Timeout das requisições (padrão: 20s)
- `--user-agent`: User-Agent customizado

## 🧪 Testes

```bash
# Teste básico da estrutura modular
python test_modular.py

# Teste do scraper original (para comparação)
python test_world_wine.py
```

## 📦 Módulos Detalhados

### models/offer.py
- `OfferItem`: Dataclass que representa uma oferta com todos os campos necessários

### protocols/base.py
- `HttpClient`: Interface para clientes HTTP
- `DetailParser`: Interface para parsers de detalhes
- `ListPageParser`: Interface para parsers de listas
- `OfferRepository`: Interface para repositórios

### clients/httpx_client.py
- `AsyncHttpxClient`: Cliente HTTP assíncrono com rate limiting, retry logic e HTTP/2

### parsers/
- `DoisPorUmListPageParser`: Extrai links de detalhes e paginação
- `DoisPorUmDetailParser`: Extrai dados completos das páginas de oferta

### repositories/pandas_repository.py
- `PandasOfferRepository`: Salva dados em CSV e JSONL usando pandas

### services/
- `LinkCollector`: Coleta links usando BFS com paginação
- `DetailScraper`: Faz scraping de detalhes com controle de concorrência
- `ScrapeCoordinator`: Orquestra todo o processo

## 🔧 Extensibilidade

### Adicionando um Novo Parser

```python
# src/parsers/new_parser.py
from src.protocols.base import DetailParser
from src.models.offer import OfferItem

class NewDetailParser:
    def parse(self, html: str, url: str) -> Optional[OfferItem]:
        # Implementar lógica específica
        return OfferItem(...)

# Uso no main.py
detail_parser = NewDetailParser()
```

### Adicionando um Novo Repositório

```python
# src/repositories/json_repository.py
from src.protocols.base import OfferRepository

class JsonOfferRepository:
    def save_csv(self, items: List[OfferItem], path: str) -> None:
        # Implementação específica
        pass
    
    def save_jsonl(self, items: List[OfferItem], path: str) -> None:
        # Implementação específica
        pass
```

## 🔍 Vantagens da Refatoração

1. **Testabilidade**: Cada componente pode ser testado isoladamente
2. **Manutenibilidade**: Mudanças em um módulo não afetam outros
3. **Reutilização**: Componentes podem ser reutilizados em outros projetos
4. **Flexibilidade**: Fácil trocar implementações (ex: httpx por requests)
5. **Legibilidade**: Código mais organizado e fácil de entender
6. **Escalabilidade**: Estrutura preparada para crescimento

## 🚧 Migração

O arquivo `scraper.py` original foi mantido para compatibilidade. Para migrar:

1. Use `main_modular.py` em vez de `scraper.py`
2. Teste com `test_modular.py`
3. Após validação, remova `scraper.py` se necessário

A API e parâmetros de linha de comando são idênticos, garantindo compatibilidade total.

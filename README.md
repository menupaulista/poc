# Scraper DoisPorUm.net

Um scraper Python desenvolvido seguindo os princípios SOLID para extrair ofertas do site doisporum.net.

## Instalação

1. Instale o uv (gerenciador de dependências):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone ou baixe o projeto e navegue até o diretório:
```bash
cd poc
```

3. Instale as dependências:
```bash
uv sync
```

## Uso

Execute o scraper com os parâmetros desejados:

```bash
uv run python scraper.py \
  --seed-url "https://doisporum.net/" \
  --max-items 120 \
  --rate-limit-seconds 0.8 \
  --max-concurrency 6 \
  --csv-path doisporum_ofertas.csv \
  --jsonl-path doisporum_ofertas.jsonl
```

### Parâmetros

- `--seed-url`: URL inicial para começar a raspagem (obrigatório)
- `--max-items`: Número máximo de itens para coletar (padrão: 120)
- `--rate-limit-seconds`: Segundos entre requisições (padrão: 0.8)
- `--max-concurrency`: Máximo de requisições simultâneas (padrão: 6)
- `--csv-path`: Caminho do arquivo CSV de saída (padrão: doisporum_ofertas.csv)
- `--jsonl-path`: Caminho do arquivo JSONL de saída (padrão: doisporum_ofertas.jsonl)
- `--timeout`: Timeout das requisições em segundos (padrão: 20.0)
- `--user-agent`: User-Agent customizado (opcional)

## Arquitetura

O projeto segue os princípios SOLID:

### Single Responsibility Principle
- `OfferItem`: Entidade de domínio representando uma oferta
- `AsyncHttpxClient`: Cliente HTTP assíncrono
- `DoisPorUmListPageParser`: Parser de páginas de listagem
- `DoisPorUmDetailParser`: Parser de páginas de detalhes
- `PandasOfferRepository`: Persistência usando pandas

### Open/Closed Principle
- Interfaces/Protocolos permitem extensão sem modificação do código existente

### Liskov Substitution Principle
- Implementações podem ser substituídas por outras que implementem o mesmo protocolo

### Interface Segregation Principle
- Protocolos específicos e focados (`HttpClient`, `DetailParser`, etc.)

### Dependency Inversion Principle
- Classes dependem de abstrações (protocolos), não de implementações concretas

## Funcionalidades

### Coleta de Links
- Coleta links que seguem o padrão `/home/details/\d+/?$`
- Segue paginações usando heurísticas múltiplas
- Normaliza URLs para absolutas

### Extração de Dados
Para cada página de detalhes, extrai:
- **ID**: Do padrão `/details/(\d+)` na URL
- **Título**: Prioridade h1 > h2 > [data-testid*="title"] > [class*="title"] > <title>
- **Oferta**: Texto que começa com "Oferta" ou contém "2 por 1", "dois por um", "2x1"
- **Descrição**: Primeiro bloco > 120 chars que não seja oferta
- **Endereço**: Bloco com CEP ou indicadores de endereço
- **Telefone**: Padrão `(XX) XXXXX-XXXX`
- **Website**: Primeiro link externo (não doisporum.net)
- **Imagens**: URLs normalizadas, preferindo srcset

### Recursos de Rede
- Cliente HTTP assíncrono com HTTP/2
- Rate limiting configurável
- Retries automáticos (até 3 tentativas)
- Controle de concorrência
- Timeout configurável

### Saída
- **CSV**: Inclui colunas `images` (string separada por vírgula) e `images_json` (JSON array)
- **JSONL**: Um objeto JSON por linha
- Ordenação por ID numérico quando possível

## Dependências

- `httpx[http2]==0.28.1`: Cliente HTTP assíncrono
- `beautifulsoup4`: Parser HTML
- `lxml`: Parser XML/HTML performático
- `pandas`: Manipulação de dados e exportação CSV
- `tqdm`: Barra de progresso

## Exemplo de Saída

O scraper salvará:
1. `doisporum_ofertas.csv` - Arquivo CSV com todas as ofertas
2. `doisporum_ofertas.jsonl` - Arquivo JSONL com uma oferta por linha

Exemplo de registro:
```json
{
  "id": "123",
  "url": "https://doisporum.net/home/details/123",
  "title": "Oferta Especial Restaurant",
  "offer": "Oferta: 2 por 1 em pratos principais",
  "description": "Descrção detalhada do restaurante e da oferta...",
  "address": "Rua das Flores, 123, São Paulo - SP, 01234-567",
  "phone": "(11) 99999-9999",
  "website": "https://restaurant.com.br",
  "images": ["https://doisporum.net/image1.jpg", "https://doisporum.net/image2.jpg"]
}
```

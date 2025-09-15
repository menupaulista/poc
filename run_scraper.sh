#!/bin/bash

# Script de exemplo para executar o scraper completo
# Como solicitado na especificação

uv run python scraper.py \
  --seed-url "https://doisporum.net/" \
  --max-items 120 \
  --rate-limit-seconds 0.8 \
  --max-concurrency 6 \
  --csv-path doisporum_ofertas.csv \
  --jsonl-path doisporum_ofertas.jsonl

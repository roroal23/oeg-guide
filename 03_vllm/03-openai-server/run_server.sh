#!/bin/bash
# Levanta vLLM en modo servidor con una API compatible con la de OpenAI en http://localhost:8000/v1

echo "Iniciando servidor vLLM para Qwen 2.5 (0.5B)"

uv run vllm serve Qwen/Qwen2.5-0.5B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --enforce-eager \
    --disable-log-stats

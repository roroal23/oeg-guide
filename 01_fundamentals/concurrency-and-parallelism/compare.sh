#!/usr/bin/env bash
# Ejecuta las cuatro versiones del mismo trabajo CPU-bound para comparar tiempos.
set -e
cd "$(dirname "$0")"

echo "=== SECUENCIAL ==="
uv run sequential.py

echo "=== CON PROCESOS ==="
uv run processes.py

echo "=== CON HILOS ==="
uv run threads.py

echo "=== CON MÉTODOS ASÍNCRONOS ==="
uv run async.py

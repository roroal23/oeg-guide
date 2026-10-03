#!/bin/bash
# Levanta el servidor vLLM, espera a que responda y prueba los tres clientes.
# Uso: desde esta carpeta -> sbatch execute_job.sh
#SBATCH --partition=standard-gpu
#SBATCH --gres=gpu:a100:1
#SBATCH --job-name=vllm_servidor
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=16G
#SBATCH --time=00:20:00
#SBATCH --output=logs/exec-%j.log
#SBATCH --error=logs/exec-%j.log

SERVER_PORT=8000
HEALTH_TIMEOUT=600
HEALTH_INTERVAL=10

PROJECT_DIR="$(dirname "$HOME")/PROJECT"
export UV_CACHE_DIR="${PROJECT_DIR}/.cache/uv"
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"

module purge
module load Python/3.11.3-GCCcore-12.3.0
# No se carga el módulo CUDA: las wheels de torch/vLLM traen su propio runtime (CUDA 13)

echo "GPUs detectadas por el sistema:"
nvidia-smi -L

# 1. Servidor en segundo plano
bash run_server.sh &
SERVER_PID=$!

# 2. Espera activa sobre /health (los clientes también reintentan, pero así fallamos antes)
elapsed=0
until curl -sf "http://localhost:${SERVER_PORT}/health" > /dev/null 2>&1; do
    if ! kill -0 "$SERVER_PID" 2> /dev/null || [ "$elapsed" -ge "$HEALTH_TIMEOUT" ]; then
        echo "ERROR: el servidor no arrancó (${elapsed}s)."
        kill "$SERVER_PID" 2> /dev/null
        exit 1
    fi
    sleep "$HEALTH_INTERVAL"
    elapsed=$(( elapsed + HEALTH_INTERVAL ))
done
echo "Servidor listo tras ${elapsed}s."

# 3. Clientes
uv run openai_client.py
uv run litellm_client.py
uv run requests_client.py

# 4. Limpieza: apagar el servidor (run_server.sh y el proceso de vLLM que cuelga de él)
pkill -P "$SERVER_PID"
kill "$SERVER_PID" 2> /dev/null
echo "Trabajo finalizado."

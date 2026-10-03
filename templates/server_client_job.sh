#!/bin/bash
# Patrón servidor + cliente en el mismo trabajo:
#   1) levanta `vllm serve` en segundo plano,
#   2) espera a que /health responda (con timeout),
#   3) lanza el cliente y guarda su código de salida,
#   4) apaga el servidor.
# Uso: desde la carpeta del proyecto -> sbatch server_client_job.sh [MODELO] [MAX_CONCURRENT]
##----------------------- Start job description -----------------------
#SBATCH --partition=standard-gpu
#SBATCH --gres=gpu:a100:1
#SBATCH --job-name=server_client
#SBATCH --ntasks=4
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --mail-type=ALL
# CONFIGURA: tu correo para los avisos de SLURM
#SBATCH --mail-user=TU_CORREO@alumnos.upm.es
#SBATCH --output=logs/exec-%j.log
#SBATCH --error=logs/exec-%j.log
##------------------------ End job description ------------------------

#== CONFIGURACIÓN ==
MODEL_NAME="${1:-Qwen/Qwen2.5-0.5B-Instruct}"
MAX_CONCURRENT="${2:-5}"
SERVER_PORT="8000"
HEALTH_TIMEOUT=600
HEALTH_INTERVAL=10
#===================

PROJECT_DIR="$(dirname "$HOME")/PROJECT"
export UV_CACHE_DIR="${PROJECT_DIR}/.cache/uv"
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"

module purge
module load Python/3.11.3-GCCcore-12.3.0   # CONFIGURA (coincidir con .python-version)
# No se carga el módulo CUDA: las wheels de torch/vLLM traen su propio runtime (CUDA 13)

echo "GPUs detectadas por el sistema:"
nvidia-smi -L

# 1. Servidor en segundo plano
echo "Iniciando vLLM con $MODEL_NAME en el puerto $SERVER_PORT..."
uv run vllm serve "$MODEL_NAME" \
    --host 0.0.0.0 \
    --port "$SERVER_PORT" \
    --max-num-seqs "$MAX_CONCURRENT" \
    --disable-log-stats &
SERVER_PID=$!

# 2. Espera activa sobre /health
echo "Esperando al servidor (timeout: ${HEALTH_TIMEOUT}s)..."
elapsed=0
ready=0
while [ "$elapsed" -lt "$HEALTH_TIMEOUT" ]; do
    if curl -sf "http://localhost:${SERVER_PORT}/health" > /dev/null 2>&1; then
        echo "Servidor listo tras ${elapsed}s."
        ready=1
        break
    fi
    if ! kill -0 "$SERVER_PID" 2> /dev/null; then
        echo "ERROR: el proceso de vLLM ha muerto antes de estar listo."
        exit 1
    fi
    sleep "$HEALTH_INTERVAL"
    elapsed=$(( elapsed + HEALTH_INTERVAL ))
done

if [ "$ready" -eq 0 ]; then
    echo "ERROR: el servidor no respondió en ${HEALTH_TIMEOUT}s. Abortando."
    kill "$SERVER_PID" 2> /dev/null
    exit 1
fi

# 3. Cliente
uv run main.py "$SERVER_PORT" "$MODEL_NAME" "$MAX_CONCURRENT"
EXIT_CODE=$?

# 4. Limpieza
echo "Cerrando el servidor de vLLM"
kill "$SERVER_PID"

echo "Trabajo finalizado con código de salida: $EXIT_CODE"
exit $EXIT_CODE

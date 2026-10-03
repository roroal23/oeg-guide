#!/bin/bash
# Benchmark (versión estructurada) contra un servidor vLLM levantado en el mismo trabajo.
# Los parámetros del modelo y de vLLM se leen del YAML de configuración.
# Uso: desde esta carpeta ->
#   sbatch execute_job.sh [MODELO] [CONFIG_YAML]
#   p. ej. sbatch execute_job.sh Qwen/Qwen2.5-7B-Instruct config.yaml
# Requiere haber hecho `uv run wandb login` una vez en Magerit.
##----------------------- Start job description -----------------------
#SBATCH --partition=standard-gpu
#SBATCH --gres=gpu:a100:1
#SBATCH --job-name=vllm_scaling_v2
#SBATCH --ntasks=4
#SBATCH --mem=48G
#SBATCH --time=10:00:00
#SBATCH --output=logs/exec-%j.log
#SBATCH --error=logs/exec-%j.log
##------------------------ End job description ------------------------

MODEL_NAME="${1:-Qwen/Qwen2.5-0.5B-Instruct}"
CONFIG="${2:-config.example.yaml}"
HEALTH_TIMEOUT=600
HEALTH_INTERVAL=10

PROJECT_DIR="$(dirname "$HOME")/PROJECT"
export UV_CACHE_DIR="${PROJECT_DIR}/.cache/uv"
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"

#0. Carga de módulos
module purge
module load Python/3.11.3-GCCcore-12.3.0
# No se carga el módulo CUDA: las wheels de torch/vLLM traen su propio runtime (CUDA 13)

echo "GPUs detectadas por el sistema:"
nvidia-smi -L

#1. Leer puerto y flags de vLLM del YAML (falla aquí si el modelo no está en la configuración)
SERVER_PORT=$(uv run python -m src.config --yaml "$CONFIG" --model "$MODEL_NAME" --port) || exit 1
VLLM_ARGS=$(uv run python -m src.config --yaml "$CONFIG" --model "$MODEL_NAME" --vllm-args) || exit 1

#2. Lanzar el servidor
echo "Iniciando vLLM con $MODEL_NAME en el puerto $SERVER_PORT ($VLLM_ARGS)..."
# shellcheck disable=SC2086  # VLLM_ARGS debe separarse en palabras
uv run vllm serve "$MODEL_NAME" \
    --host 0.0.0.0 \
    --port "$SERVER_PORT" \
    $VLLM_ARGS \
    --disable-log-stats &
SERVER_PID=$!

#3. Espera activa sobre /health
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

#4. Lanzar el cliente
uv run python -m src.benchmark --yaml "$CONFIG" --model "$MODEL_NAME" --job-id "$SLURM_JOB_ID"
BENCHMARK_EXIT_CODE=$?

#5. Limpieza
echo "Cerrando el servidor de vLLM"
kill "$SERVER_PID"

echo "Trabajo finalizado con código de salida: $BENCHMARK_EXIT_CODE"
exit $BENCHMARK_EXIT_CODE

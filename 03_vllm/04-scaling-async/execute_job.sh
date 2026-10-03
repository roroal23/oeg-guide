#!/bin/bash
# Benchmark asíncrono contra un servidor vLLM levantado en el mismo trabajo.
# Uso: desde esta carpeta ->
#   sbatch execute_job.sh [MAX_CONCURRENT] [MODELO] [TOTAL_SAMPLES]
#   p. ej. sbatch execute_job.sh 10 Qwen/Qwen2.5-7B-Instruct 9500
# Requiere haber hecho `uv run wandb login` una vez en Magerit.
##----------------------- Start job description -----------------------
#SBATCH --partition=standard-gpu
#SBATCH --gres=gpu:a100:1
#SBATCH --job-name=vllm_scaling
#SBATCH --ntasks=4
#SBATCH --mem=48G
#SBATCH --time=10:00:00
#SBATCH --output=logs/exec-%j.log
#SBATCH --error=logs/exec-%j.log
##------------------------ End job description ------------------------

#== CONFIGURACIÓN DEL EXPERIMENTO ==
MAX_CONCURRENT="${1:-5}"
MODEL_NAME="${2:-Qwen/Qwen2.5-0.5B-Instruct}"
TOTAL_SAMPLES="${3:-9500}"
SERVER_PORT="8000"

MAX_MODEL_LEN="2048"
HEALTH_TIMEOUT=600
HEALTH_INTERVAL=10
#===================================

PROJECT_DIR="$(dirname "$HOME")/PROJECT"
export UV_CACHE_DIR="${PROJECT_DIR}/.cache/uv"
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"

#0. Carga de módulos
module purge
module load Python/3.11.3-GCCcore-12.3.0
# No se carga el módulo CUDA: las wheels de torch/vLLM traen su propio runtime (CUDA 13)

#1. Verificación de la GPU asignada
echo "GPUs detectadas por el sistema:"
nvidia-smi -L

#2. Lanzar el servidor
echo "Iniciando servidor vLLM con el modelo $MODEL_NAME en el puerto $SERVER_PORT..."
uv run vllm serve "$MODEL_NAME" \
    --host 0.0.0.0 \
    --port "$SERVER_PORT" \
    --dtype bfloat16 \
    --max-model-len "$MAX_MODEL_LEN" \
    --max-num-seqs "$MAX_CONCURRENT" \
    --gpu-memory-utilization 0.90 \
    --disable-log-stats &

SERVER_PID=$! #pid del servidor vLLM

#3. Espera activa: polling al endpoint /health de vLLM
echo "Esperando a que el servidor esté listo (timeout: ${HEALTH_TIMEOUT}s)..."
elapsed=0
ready=0

while [ "$elapsed" -lt "$HEALTH_TIMEOUT" ]; do
    if curl -sf "http://localhost:${SERVER_PORT}/health" > /dev/null 2>&1; then
        echo "Servidor listo tras ${elapsed}s. Lanzando experimento"
        ready=1
        break
    fi

    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "ERROR: El proceso vLLM ha muerto antes de estar listo"
        exit 1
    fi

    sleep "$HEALTH_INTERVAL"
    elapsed=$(( elapsed + HEALTH_INTERVAL ))
done

if [ "$ready" -eq 0 ]; then
    echo "ERROR: El servidor no respondió en ${HEALTH_TIMEOUT}s. Abortando"
    kill "$SERVER_PID" 2> /dev/null
    exit 1
fi

#4. Lanzar el cliente
uv run benchmark.py "$SLURM_JOB_ID" "$SERVER_PORT" "$MODEL_NAME" "$TOTAL_SAMPLES" "$MAX_CONCURRENT"
BENCHMARK_EXIT_CODE=$?

#5. Limpieza
echo "Cerrando el servidor de vLLM"
kill "$SERVER_PID"

echo "Trabajo finalizado con código de salida: $BENCHMARK_EXIT_CODE"
exit $BENCHMARK_EXIT_CODE

#!/bin/bash
# Lanza un benchmark para varios modelos, uno detrás de otro.
# Uso: desde esta carpeta ->
#   sbatch execute_job.sh                                   # benchmark.py con los modelos por defecto
#   sbatch execute_job.sh benchmark_speed.py            # otro script, modelos por defecto
#   sbatch execute_job.sh benchmark.py Qwen/Qwen2.5-7B-Instruct   # script y modelos a elegir
# Requiere haber hecho `uv run wandb login` una vez en Magerit (guarda la clave en ~/.netrc).
#SBATCH --partition=standard-gpu
#SBATCH --gres=gpu:a100:1
#SBATCH --job-name=benchmark_wandb
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=logs/exec-%j.log
#SBATCH --error=logs/exec-%j.log

SCRIPT="${1:-benchmark.py}"
shift
MODELS=("$@")
if [ ${#MODELS[@]} -eq 0 ]; then
    # Para el 7B pásalo como argumento y sube --mem (con 16 GB de RAM no cabía).
    MODELS=("Qwen/Qwen2.5-0.5B-Instruct" "Qwen/Qwen2.5-1.5B-Instruct" "Qwen/Qwen2.5-3B-Instruct")
fi

PROJECT_DIR="$(dirname "$HOME")/PROJECT"
export UV_CACHE_DIR="${PROJECT_DIR}/.cache/uv"
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"

module purge
module load Python/3.11.3-GCCcore-12.3.0
# No se carga el módulo CUDA: las wheels de torch/vLLM traen su propio runtime (CUDA 13)

nvidia-smi -L

echo "Iniciando $SCRIPT..."
for model in "${MODELS[@]}"; do
    uv run "$SCRIPT" "$model"
done
echo "Trabajo finalizado."

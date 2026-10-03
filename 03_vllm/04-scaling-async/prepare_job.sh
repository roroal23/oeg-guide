#!/bin/bash
# Prepara el entorno con uv. Uso: desde esta carpeta -> sbatch prepare_job.sh
#SBATCH --partition=debug
#SBATCH --job-name=prep_vllm_scaling
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=4G
#SBATCH --time=00:10:00
#SBATCH --output=logs/prep-%j.log
#SBATCH --error=logs/prep-%j.log

PROJECT_DIR="$(dirname "$HOME")/PROJECT"
export UV_CACHE_DIR="${PROJECT_DIR}/.cache/uv"
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"

module purge
module load Python/3.11.3-GCCcore-12.3.0
# No se carga el módulo CUDA: las wheels de torch/vLLM traen su propio runtime (CUDA 13)

echo "Sincronizando entorno virtual con uv..."
uv sync --no-install-project
echo "Entorno preparado."

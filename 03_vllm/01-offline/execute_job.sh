#!/bin/bash
# Ejecuta uno de los scripts de vLLM offline en una GPU.
# Uso: desde esta carpeta ->
#   sbatch execute_job.sh                      # vllm_inspector.py
#   sbatch execute_job.sh sampling_params.py
#SBATCH --partition=standard-gpu
#SBATCH --gres=gpu:a100:1
#SBATCH --job-name=vllm_offline
#SBATCH --ntasks=1
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --output=logs/exec-%j.log
#SBATCH --error=logs/exec-%j.log

SCRIPT="${1:-vllm_inspector.py}"

PROJECT_DIR="$(dirname "$HOME")/PROJECT"
export UV_CACHE_DIR="${PROJECT_DIR}/.cache/uv"
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"

module purge
module load Python/3.11.3-GCCcore-12.3.0
# No se carga el módulo CUDA: las wheels de torch/vLLM traen su propio runtime (CUDA 13)

nvidia-smi -L
uv run "$SCRIPT"

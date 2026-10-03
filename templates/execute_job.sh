#!/bin/bash
# Ejecuta el programa del proyecto en una GPU.
# Uso: desde la carpeta del proyecto -> sbatch execute_job.sh [argumentos para main.py]
##----------------------- Start job description -----------------------
#SBATCH --partition=standard-gpu
# GPU: gpu:a100:1, o gpu:v100:1 (16 GB, sin bfloat16; las versiones recientes de torch/vLLM, compiladas para CUDA 13, ya no la soportan)
#SBATCH --gres=gpu:a100:1
#SBATCH --job-name=execute_job
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=16G
#SBATCH --time=01:00:00
#SBATCH --mail-type=ALL
# CONFIGURA: tu correo para los avisos de SLURM
#SBATCH --mail-user=TU_CORREO@alumnos.upm.es
#SBATCH --output=logs/exec-%j.log
#SBATCH --error=logs/exec-%j.log
##------------------------ End job description ------------------------

# 0. Cachés fuera del $HOME
PROJECT_DIR="$(dirname "$HOME")/PROJECT"
export UV_CACHE_DIR="${PROJECT_DIR}/.cache/uv"
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"

# 1. Carga de módulos (misma versión que en prepare_job.sh)
module purge
module load Python/3.12.3-GCCcore-13.3.0   # CONFIGURA
# module load CUDA/12.1.1   # solo si tu código compila extensiones CUDA; torch trae su propio runtime

# 2. Verificación de la GPU asignada
echo "GPUs detectadas por el sistema:"
nvidia-smi -L

# 3. Lanzar el programa. "$@" reenvía los argumentos de sbatch al script
echo "Iniciando programa..."
uv run main.py "$@"
EXIT_CODE=$?

echo "Trabajo finalizado con código de salida: $EXIT_CODE"
exit $EXIT_CODE

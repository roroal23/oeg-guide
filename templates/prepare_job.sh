#!/bin/bash
# Prepara el entorno virtual del proyecto con uv (no necesita GPU).
# Uso: desde la carpeta del proyecto -> sbatch prepare_job.sh
##----------------------- Start job description -----------------------
#SBATCH --partition=debug
#SBATCH --job-name=prepare_job
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=4G
#SBATCH --time=00:10:00
#SBATCH --mail-type=ALL
# CONFIGURA: tu correo para los avisos de SLURM
#SBATCH --mail-user=TU_CORREO@alumnos.upm.es
#SBATCH --output=logs/prep-%j.log
#SBATCH --error=logs/prep-%j.log
##------------------------ End job description ------------------------
# Sin --chdir: SLURM ejecuta el trabajo en el directorio desde el que lanzas sbatch.
# La carpeta logs/ debe existir antes de lanzar (si no, SLURM no puede escribir el log).

# 0. Cachés fuera del $HOME (cuota pequeña). PROJECT está en /home/<code>/PROJECT
PROJECT_DIR="$(dirname "$HOME")/PROJECT"
export UV_CACHE_DIR="${PROJECT_DIR}/.cache/uv"
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"

# 1. Carga de módulos. La versión de Python debe coincidir con .python-version
module purge
module load Python/3.12.3-GCCcore-13.3.0   # CONFIGURA (3.11 -> Python/3.11.3-GCCcore-12.3.0)
# module load CUDA/12.1.1   # solo si tu código compila extensiones CUDA; torch trae su propio runtime

# 2. Sincronización del entorno con uv (lee pyproject.toml y uv.lock)
uv --version
echo "Sincronizando entorno virtual con uv..."
uv sync --no-install-project

# 3. Verificación (opcional)
uv pip list

echo "Entorno preparado con éxito."

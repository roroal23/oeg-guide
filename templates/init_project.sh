#!/bin/bash
# Define la función `init_project`, que crea un proyecto uv listo para Magerit:
#   - pyproject.toml, .python-version y main.py (uv init)
#   - carpeta logs/ para las salidas de SLURM
#   - prepare_job.sh y execute_job.sh copiados de estas plantillas
#
# Uso (en Magerit o en local):
#   source templates/init_project.sh
#   init_project <nombre_proyecto> <correo@alumnos.upm.es> [version_python]
#
# Ejemplo:
#   init_project mi_experimento nombre.apellido@alumnos.upm.es 3.11

TEMPLATES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

init_project() {
    if [ "$#" -lt 2 ]; then
        echo "Uso: init_project <nombre_proyecto> <correo@alumnos.upm.es> [version_python]"
        return 1
    fi

    local proj_name=$1
    local email=$2
    local py_version=${3:-3.12}
    local py_module

    case "$py_version" in
        3.11) py_module="Python/3.11.3-GCCcore-12.3.0" ;;
        3.12) py_module="Python/3.12.3-GCCcore-13.3.0" ;;
        *)
            echo "Versión de Python no contemplada: $py_version (usa 3.11 o 3.12)"
            return 1
            ;;
    esac

    # 1. Proyecto uv (crea pyproject.toml, .python-version, main.py y README.md)
    echo "Creando proyecto: $proj_name (Python $py_version)..."
    uv init --python "$py_version" "$proj_name" || return 1
    mkdir -p "$proj_name/logs"
    touch "$proj_name/logs/.gitkeep"

    # 2. Scripts de SLURM con el correo y el módulo de Python adecuados
    local script
    for script in prepare_job.sh execute_job.sh; do
        sed -e "s/TU_CORREO@alumnos.upm.es/$email/" \
            -e "s|Python/3\.12\.3-GCCcore-13\.3\.0|$py_module|" \
            -e "s/--job-name=\(prepare\|execute\)_job/--job-name=\1_$proj_name/" \
            "$TEMPLATES_DIR/$script" > "$proj_name/$script"
        chmod +x "$proj_name/$script"
    done

    echo "------------------------------------------------"
    echo "Proyecto '$proj_name' creado."
    echo "  cd $proj_name"
    echo "  uv add <dependencias>            # p. ej. uv add torch transformers"
    echo "  sbatch prepare_job.sh            # en Magerit: crea el entorno"
    echo "  sbatch execute_job.sh            # en Magerit: ejecuta main.py en GPU"
    echo "------------------------------------------------"
}

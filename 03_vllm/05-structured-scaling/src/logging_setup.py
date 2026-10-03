"""
Configuración centralizada del sistema de logging.
"""
from __future__ import annotations

import logging
import sys


def setup_logging(job_id: str, model_safe_name: str = "") -> logging.Logger:
    """
    Configura y devuelve el logger principal del benchmark.

    El formato incluye job_id y modelo para que cada línea sea autocontenida.
    Se escribe a stdout para que SLURM lo capture en el fichero de log del job.

    Args:
        job_id: ID del job SLURM (o 'local' en ejecución local).
        model_safe_name: Nombre del modelo sin '/', vacío si aún no se ha
                         seleccionado modelo.
    """
    logger = logging.getLogger("benchmark")

    # Evitar duplicar handlers si se llama varias veces (ejecución de tests)
    if logger.handlers:
        logger.handlers.clear()

    context = f"job={job_id}"
    if model_safe_name:
        context += f" model={model_safe_name}"

    formatter = logging.Formatter(
        fmt=f"%(asctime)s [%(levelname)s] [{context}] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # evitar doble log si hay logger raíz configurado

    return logger

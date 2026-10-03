"""
Configuracion del experimento, leida y validada desde un YAML (ver config.example.yaml).

Tambien se puede usar desde bash para que el YAML sea la unica fuente de verdad:
    uv run python -m src.config --yaml config.example.yaml --model <modelo> --vllm-args
    uv run python -m src.config --yaml config.example.yaml --model <modelo> --port
"""
from __future__ import annotations

import os
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

class VllmConfig(BaseModel):
    """Parametros pasados a vllm serve (bfloat16 requiere GPU con compute capability >= 8.0, p. ej. A100)"""
    dtype: str = "bfloat16"
    max_model_len: int = Field(gt=0)
    max_num_seqs: int = Field(gt=0)
    gpu_memory_utilization: float = Field(gt=0, le=1)

    def to_cli_args(self) -> str:
        """Convierte los campos en flags de `vllm serve` (max_model_len -> --max-model-len 2048)"""
        return " ".join(
            f"--{field.replace('_', '-')} {value}" for field, value in self.model_dump().items()
        )

class ModelConfig(BaseModel):
    """Configuracion de un modelo dentro del experimento"""
    enabled: bool = True
    name: str
    port: int = Field(default=8000, gt=0)
    max_concurrent_requests: int = Field(default=1, gt=0)
    vllm: VllmConfig

    @property
    def safe_name(self) -> str:
        """Nombre seguro para usar en rutas de archivos"""
        return self.name.replace("/", "_")
    
    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El nombre del modelo no puede estar vacío")
        return v.strip()
    
class GlobalConfig(BaseModel):
    """Configuracion global del experimento"""
    job_id: str
    dataset_name: str
    dataset_split: str
    total_samples: int = Field(default=50, gt=0, description="Numero de filas a procesar")
    output_dir: Path = Path("./outputs")
    wandb_project: str
    system_prompt: str
    health_timeout: int = Field(default=600, gt=0, description="Tiempo máximo de espera")
    health_interval: int = Field(default=10, gt=0, description="Intervalo de tiempo entre healthchecks")

    @field_validator("system_prompt")
    @classmethod
    def prompt_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El prompt del sistema no puede estar vacío")
        return v.strip()
    
class ExperimentConfig(BaseModel):
    """Raiz de la configuracion. Se construye con from_yaml()"""

    #'global' es una palabra reservada en Python, por lo que usamos 'global_' como nombre de atributo
    global_: GlobalConfig = Field(alias="global")
    models: list[ModelConfig]

    model_config = {"populate_by_name": True}

    @classmethod
    def from_yaml(cls, path: Path, job_id: str | None = None) -> ExperimentConfig:
        """Carga y valida el fichero YAML maestro"""

        if not path.exists():
            raise FileNotFoundError(f"Fichero de configuracion no encontrado: {path}")
        raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
        resolved_job_id = job_id or os.environ.get("SLURM_JOB_ID", "local")
        raw["global"]["job_id"] = resolved_job_id
        return cls.model_validate(raw)
    
    @property
    def active_models(self) -> list[ModelConfig]:
        """Devuelve la lista de modelos habilitados"""
        return [m for m in self.models if m.enabled]
    
    def get_model(self, name: str) -> ModelConfig:
        """Devuelve la configuracion de un modelo por nombre"""
        for m in self.models:
            if m.name == name:
                return m
        raise ValueError(f"Modelo no encontrado en la configuracion: {name}")


if __name__ == "__main__":
    parser = ArgumentParser(description="Consulta la configuracion de un modelo desde bash")
    parser.add_argument("--yaml", required=True, type=Path)
    parser.add_argument("--model", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--vllm-args", action="store_true", help="Flags para vllm serve")
    group.add_argument("--port", action="store_true", help="Puerto del servidor")
    args = parser.parse_args()

    model = ExperimentConfig.from_yaml(args.yaml).get_model(args.model)
    print(model.vllm.to_cli_args() if args.vllm_args else model.port)

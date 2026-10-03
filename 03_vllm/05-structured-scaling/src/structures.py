# pylint: disable=missing-function-docstring
"""
Definicion de estructuras para almacenar los resultados del experimento
"""

from __future__ import annotations
from datetime import datetime, timezone

from litellm import ModelResponse
from pydantic import BaseModel, Field, field_validator


class InferenceMetrics(BaseModel):
    """Metricas de consumo de tokens del modelo, extraidas de LiteLLM"""
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    latency_s: float = Field(ge=0.0)

    @classmethod
    def from_response(cls, response: ModelResponse, latency_s: float) -> InferenceMetrics:
        usage = response["usage"] or {}
        return cls(
            prompt_tokens = usage.get("prompt_tokens", 0),
            completion_tokens = usage.get("completion_tokens", 0),
            total_tokens = usage.get("total_tokens", 0),
            latency_s = latency_s,
        )

class ExperimentRecord(BaseModel):
    """
    Estructura y valida de forma estricta cada registro que se guardara en el fichero
    de resultados del experimento
    """
    record_id: int = Field(ge=0, description="Identificador unico del registro (indice de la fila)")
    job_id: str
    model: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    input_sentence: str
    model_output: str
    metrics: InferenceMetrics

    @field_validator("model_output")
    @classmethod
    def output_not_none(cls, v: str) -> str:
        return v or ""

    @classmethod
    def from_response(cls, record_id: int, job_id: str,
                    model_name:str, sentence:str, response: ModelResponse, metrics: InferenceMetrics) -> ExperimentRecord:
        """Factory: construye el registro a partir de la respuesta de LiteLLM"""
        return cls(
            record_id = record_id,
            job_id = job_id,
            model = model_name,
            input_sentence = sentence,
            model_output = response.choices[0].message.content or "",
            metrics = metrics
        )

    def to_jsonl_dict(self) -> dict:
        """Serializacion para JSON""" 
        d = self.model_dump()
        d["timestamp"] = self.timestamp.isoformat()
        return d

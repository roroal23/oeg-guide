"""
Definicion de estructuras para almacenar los resultados del experimento
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import  Dict, Any
from litellm import ModelResponse
from datetime import datetime, timezone

@dataclass(frozen = True)
class UsageMetrics:
    """Metricas de consumo de tokens del modelo, extraidas de ResponseModel de LiteLLM"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

@dataclass(frozen = True)
class ExperimentRecord:
    """
    Estructura y valida de forma estricta cada registro que se guardara en el fichero
    de resultados del experimento
    """
    record_id: int
    timestamp: str
    model: str
    input_sentence: str
    model_output: str
    usage_metrics: UsageMetrics

    @classmethod
    def from_response(cls, record_id: int,
                    model_name:str, sentence:str, response: ModelResponse) -> ExperimentRecord:
        """Metodo de factoria para construir el registro a partir de la respuesta de LiteLLM"""
        return cls(
            record_id = record_id,
            timestamp = datetime.now(timezone.utc).isoformat(),
            model = model_name,
            input_sentence = sentence,
            model_output = response.choices[0].message.content or "",
            usage_metrics = UsageMetrics(
                prompt_tokens = response["usage"]["prompt_tokens"] or 0,
                completion_tokens = response["usage"]["completion_tokens"] or 0,
                total_tokens = response["usage"]["total_tokens"] or 0,
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la estructura de datos en un diccionario serializable"""
        return asdict(self)

"""
Observabilidad del experimento con Weights & Biases.

WandbLogger encapsula el ciclo de vida completo de un run de W&B:
inicialización, logging incremental por inferencia y cierre con resumen.

El logging es no bloqueante para los productores: log_inference() y log_error()
solo hacen queue.put(), que es O(1). La tarea _consumer_task() es la única
que llama a wandb.log(), serializando las escrituras a la API de W&B.
Al cerrar, se sube además una tabla con un ejemplo por fila (prompt y respuesta).

Esto evita que una latencia puntual de la API de W&B ralentice las inferencias.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import wandb
from pydantic import BaseModel, Field

from .structures import ExperimentRecord, InferenceMetrics

logger = logging.getLogger("benchmark")

# Sentinel interno: señal de fin para el consumer
_STOP = object()


class RunSummary(BaseModel):
    """Métricas agregadas al final del experimento, loggeadas en W&B y devueltas a main()."""

    completed: int = Field(ge=0, default=0)
    errors: int = Field(ge=0, default=0)
    skipped: int = Field(ge=0, default=0)
    total_tokens: int = Field(ge=0, default=0)
    total_latency_s: float = Field(ge=0.0, default=0.0)
    duration_s: float = Field(ge=0.0, default=0.0)

    @property
    def avg_latency_s(self) -> float:
        return self.total_latency_s / self.completed if self.completed else 0.0

    @property
    def avg_tokens(self) -> float:
        return self.total_tokens / self.completed if self.completed else 0.0

    @property
    def throughput_per_min(self) -> float:
        return (self.completed / self.duration_s * 60) if self.duration_s else 0.0


class WandbLogger:
    """
    Logger de observabilidad para un experimento (un modelo, un job).

    Ciclo de vida:
        wandb_logger = WandbLogger(...)
        await wandb_logger.start()          # en main(), antes de run_experiment()
        ...
        await wandb_logger.log_inference()  # en cada productor
        await wandb_logger.log_error()      # en cada productor que falla
        ...
        summary = await wandb_logger.stop() # en main(), tras run_experiment()
    """

    def __init__(self, project: str, run_name: str, config: dict[str, Any]) -> None:
        self._project = project
        self._run_name = run_name
        self._config = config
        self._queue: asyncio.Queue = asyncio.Queue()
        self._consumer: asyncio.Task | None = None
        self._start_time: float = 0.0
        self._skipped: int = 0  # fijado en stop(), viene de run_experiment
        self._samples = wandb.Table(columns=[
            "ID", "Prompt", "Response", "Prompt Tokens", "Completion Tokens", "Latency (s)"
        ])

    async def start(self) -> None:
        """
        Inicializa el run de W&B y arranca la tarea consumidora de métricas.
        Debe llamarse antes de cualquier log_inference() o log_error().
        """
        wandb.init(
            project=self._project,
            name=self._run_name,
            config=self._config,
            reinit=True,
        )
        self._start_time = time.monotonic()
        self._consumer = asyncio.create_task(self._consumer_task())
        logger.info("WandbLogger iniciado — run: %s", self._run_name)

    async def log_inference(self, metrics: InferenceMetrics, record: ExperimentRecord) -> None:
        """
        Encola las métricas (y el registro, para la tabla de ejemplos) de una inferencia completada.

        No bloqueante: solo hace queue.put(). El consumer las procesa
        en background sin interferir con los productores.
        """
        await self._queue.put((metrics, record))

    async def log_error(self) -> None:
        """
        Registra un fallo de inferencia.
        Encola un marcador de error para que el consumer actualice el contador.
        """
        await self._queue.put(None)

    async def stop(self, skipped: int = 0) -> RunSummary:
        """
        Cierra el logger limpiamente:
            1. Envía el sentinel para que el consumer termine su loop.
            2. Espera a que el consumer drene la queue y calcule el resumen.
            3. Loggea el resumen en W&B y llama a wandb.finish().

        Args:
            skipped: filas del dataset saltadas por StopIteration,
                     informado por run_experiment().

        Returns:
            RunSummary con las métricas agregadas del experimento.
        """
        if self._consumer is None:
            raise RuntimeError("WandbLogger.stop() llamado sin haber llamado start()")

        self._skipped = skipped
        await self._queue.put(_STOP)
        summary = await self._consumer

        wandb.log({
            "summary/completed": summary.completed,
            "summary/errors": summary.errors,
            "summary/skipped": summary.skipped,
            "summary/total_tokens": summary.total_tokens,
            "summary/avg_latency_s": summary.avg_latency_s,
            "summary/avg_tokens": summary.avg_tokens,
            "summary/throughput_per_min": summary.throughput_per_min,
            "summary/duration_s": summary.duration_s,
            "evaluation/text_samples": self._samples,
        })
        wandb.finish()
        logger.info(
            "WandbLogger cerrado — completados: %d, errores: %d, saltados: %d",
            summary.completed, summary.errors, summary.skipped,
        )
        return summary

    async def stop_with_error(self, error_msg: str) -> None:
        """
        Cierre de emergencia ante una excepción no recuperable en main().
        Loggea el error en W&B y cierra sin esperar al consumer.
        """
        if self._consumer is not None and not self._consumer.done():
            self._consumer.cancel()
        wandb.log({"status": "failed", "error": error_msg})
        wandb.finish()
        logger.error("WandbLogger cerrado por error: %s", error_msg)

    # ------------------------------------------------------------------
    # Implementación interna
    # ------------------------------------------------------------------

    async def _consumer_task(self) -> RunSummary:
        """
        Tarea dedicada que consume la queue y llama a wandb.log().

        Es la única parte del sistema que escribe a W&B, serializando
        las llamadas a la API para evitar concurrencia sobre el cliente.
        """
        step = 0
        completed = errors = total_tokens = 0
        total_latency = 0.0

        while True:
            item = await self._queue.get()

            if item is _STOP:
                break

            if item is None:
                # Marcador de error de log_error()
                errors += 1
                self._queue.task_done()
                continue

            # item es (InferenceMetrics, ExperimentRecord)
            metrics: InferenceMetrics
            record: ExperimentRecord
            metrics, record = item
            completed += 1
            total_tokens += metrics.total_tokens
            total_latency += metrics.latency_s

            wandb.log(
                {
                    "inference/latency_s": metrics.latency_s,
                    "inference/prompt_tokens": metrics.prompt_tokens,
                    "inference/completion_tokens": metrics.completion_tokens,
                    "inference/total_tokens": metrics.total_tokens,
                },
                step=step,
            )
            self._samples.add_data(
                record.record_id, record.input_sentence, record.model_output,
                metrics.prompt_tokens, metrics.completion_tokens, metrics.latency_s,
            )
            step += 1
            self._queue.task_done()

        duration = time.monotonic() - self._start_time
        return RunSummary(
            completed=completed,
            errors=errors,
            skipped=self._skipped,
            total_tokens=total_tokens,
            total_latency_s=total_latency,
            duration_s=duration,
        )
"""
Modulo de orquestacion asincrona para evaluacion de modelos
Carga un dataset linguistico en modo Streaming y procesa de forma concurrente
las frases enviandolas al servidor local vLLM a traves de LiteLLM
Controla el flujo de peticiones usando un semaforo asincrono; un unico 'writer'
escribe los resultados en un JSONL y un consumidor envia las metricas a W&B.

Uso (desde la carpeta del proyecto):
    uv run python -m src.benchmark --yaml config.example.yaml --model Qwen/Qwen2.5-0.5B-Instruct --job-id local
"""

from argparse import Namespace, ArgumentParser

import logging
import asyncio

from pathlib import Path
from typing import  TypeAlias, Any

from datasets import load_dataset
import litellm

from .config import GlobalConfig, ModelConfig, ExperimentConfig
from .logging_setup import setup_logging
from .wandb_logger import WandbLogger, RunSummary
from .client import LiteLLMClient
from .structures import ExperimentRecord, InferenceMetrics
from .writer import writer_task

#======= LOGS =======
logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
litellm.suppress_debug_info = True #Desactivar debug logs de LiteLLM
#======= TIPOS =======
ChatMessage : TypeAlias = dict[str, str]
#=====================

def _parse_args() -> Namespace:
    parser = ArgumentParser(description = "Benchmark de un modelo LLM individual")
    parser.add_argument("--yaml", required = True, type = Path, help = "Ruta al fichero de configuracion del experimento")
    parser.add_argument("--model", required = True, type = str, help = "Nombre completo del modelo a usar")
    parser.add_argument("--job-id", required = True, type = str, help = "ID del trabajo")
    return parser.parse_args()



async def process_prompt(row: dict[str, Any], row_id: int, job_id: str, system_prompt: str, client: LiteLLMClient,
                          sem: asyncio.Semaphore, queue: asyncio.Queue, wandb_logger: WandbLogger):
    """
    Prepara los mensajes de una frase, pide la respuesta al servidor, extrae el texto junto a las 
    metricas los tokens y lo manda a guardar
    """
    async with sem:
        logger = logging.getLogger("benchmark")
        user_prompt: str = row["Sentence"]
        messages: list[ChatMessage] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        start: float = asyncio.get_event_loop().time()
        response = await client.send_prompt(messages)
        latency: float = asyncio.get_event_loop().time() - start

        if response is None:
            logger.warning("fila %d: respuesta nula, saltando registro", row_id)
            await wandb_logger.log_error()
            return

        metrics: InferenceMetrics = InferenceMetrics.from_response(
            response = response,
            latency_s = latency
        )
        record: ExperimentRecord = ExperimentRecord.from_response(
            record_id = row_id,
            job_id = job_id,
            model_name = client.model_name,
            sentence = user_prompt,
            response = response,
            metrics = metrics
        )

        await wandb_logger.log_inference(metrics, record)
        await queue.put(record)
        logger.info("Fila %d procesada (%d tokens)", row_id, metrics.total_tokens)

        
async def run_experiment(global_config: GlobalConfig, model_config: ModelConfig, logger: logging.Logger, wandb_logger: WandbLogger) -> dict[str, int]:
    """Ejecuta el experimento completo para un modelo"""
    client = LiteLLMClient(
        base_url = f"http://localhost:{model_config.port}",
        model = model_config.name
    )
    #Preparar y conectar al modelo
    if not await client.wait_and_connect(global_config.health_timeout, global_config.health_interval):
        raise RuntimeError(f"No se pudo conectar al servidor vLLM para {model_config.name}")
    
    #Preparar el directorio y fichero de almacenamiento
    global_config.output_dir.mkdir(exist_ok = True)
    output_file : Path = global_config.output_dir / f"output_{global_config.job_id}_{model_config.safe_name}.jsonl"

    #La cola tiene capacidad limitada para evitar acumulacion excesiva en memoria
    queue: asyncio.Queue[ExperimentRecord | None] = asyncio.Queue(
        maxsize = model_config.max_concurrent_requests * 4
    )
    sem: asyncio.Semaphore  = asyncio.Semaphore(model_config.max_concurrent_requests)

    #Arrancar el writer como tarea independientes ANTES de los productores
    writer = asyncio.create_task(writer_task(queue, output_file))
    
    #Carga del dataset en modo Streaming
    logger.info("Cargando dataset %s (split %s, samples %d)", 
                global_config.dataset_name, global_config.dataset_split, global_config.total_samples)
    dataset = iter(
        load_dataset(global_config.dataset_name, split = global_config.dataset_split, streaming = True)
    )
    
    tasks = []
    skipped = 0
    for row_id in range(global_config.total_samples):
        try:
            row = next(dataset)
        except StopIteration:
            logger.warning("Dataset agotado en fila %d (< %d samples)", row_id, global_config.total_samples)
            skipped = global_config.total_samples - row_id
            break
        tasks.append(
            asyncio.create_task(
                process_prompt(row, row_id, global_config.job_id, global_config.system_prompt, client, sem, queue, wandb_logger)
            )
        )

    logger.info("%d tareas creadas. Esperando resolucion con limite de %d llamadas concurrentes",
                len(tasks), model_config.max_concurrent_requests)

    #Esperar a que todos los productores terminen
    results = await asyncio.gather(*tasks, return_exceptions = True)
    errors = sum( 1 for r in results if isinstance(r, Exception))
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error("Tarea %d fallo con excepcion: %s", i, r)

    #Señal de fin al writer
    await queue.put(None)
    written, write_errors = await writer
        
    return {
        "completed": written,
        "errors": errors + write_errors,
        "skipped": skipped
    }

async def main():
    args = _parse_args()
    config = ExperimentConfig.from_yaml(args.yaml, args.job_id)
    model_config = config.get_model(args.model)
    global_config = config.global_

    logger = setup_logging(global_config.job_id, model_config.safe_name)
    logger.info("Iniciando experimento, modelo : %s", model_config.name)

    wandb_logger : WandbLogger = WandbLogger(
        project = global_config.wandb_project,
        run_name = f"{model_config.safe_name}_{global_config.job_id}",
        config = {
            "job_id": global_config.job_id,
            "model": model_config.name,
            "dataset": global_config.dataset_name,
            "split": global_config.dataset_split,
            "total_samples": global_config.total_samples,
            "max_concurrent": model_config.max_concurrent_requests,
            **model_config.vllm.model_dump(),
        }
    )
    await wandb_logger.start()

    try:
        result = await run_experiment(global_config, model_config, logger, wandb_logger)
        summary: RunSummary = await wandb_logger.stop(skipped = result["skipped"])
        logger.info(
            "Experimento finalizado. Completados: %d, errores: %d, "
            "tokens promedio: %.1f, latencia promedio: %.2fs, throughput: %.1f/min",
            summary.completed, summary.errors, 
            summary.avg_tokens, summary.avg_latency_s, summary.throughput_per_min
        )
    except Exception as e:
        logger.error("Experimento fallido: %s", e)
        await wandb_logger.stop_with_error(str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())

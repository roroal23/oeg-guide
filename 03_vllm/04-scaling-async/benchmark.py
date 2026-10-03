"""
Modulo de orquestacion asincrona para evaluacion de modelos
Carga un dataset linguistico en modo Streaming y procesa de forma concurrente
las frases enviandolas al servidor local vLLM a traves de LiteLLM
Controla el flujo de peticiones usando un semaforo asincrono y almacena los 
resultados (con I/O no bloqueante) en un archivo Json Lines
"""
import logging
import asyncio
import json
import sys
from pathlib import Path
from typing import Tuple, List, Dict, TypeAlias, Any

import wandb
from datasets import load_dataset, IterableDataset
import litellm
from litellm import ModelResponse

from client import LiteLLMClient
from structures import ExperimentRecord

#======= CONFIGURACION =======
DATASET_NAME: str   = "nbel/EsCoLA"
DATASET_SPLIT: str  = "train"
OUTPUT_DIR: Path    = Path("./outputs")
SYSTEM_PROMPT: str  = """
Eres un experto en la lengua española.
Debes evaluar si la siguiente frase es correcta o no acorde a tu criterio.
Responde indicando si es 'Correcta' o 'Incorrecta', y luego brinda una breve explicación
de tu veredicto
"""
#======= LOGS =======
logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
litellm.suppress_debug_info = True #Desactivar debug logs de LiteLLM
#======= TIPOS =======
ChatPrompt: TypeAlias = List[Dict[str,str]]
#=====================

def get_config() -> Tuple[str, str, str, int, int]:
    """
    Obtiene la configuracion (parte dinamica) que usaremos durante el experimento.
    Espera: 
        JOB_ID: Numero de trabajo
        PORT: Numero de puerto del servidor local
        MODEL_NAME: Nombre completo del modelo
        TOTAL_SAMPLES: Filas del dataset a procesar
        MAX_CONCURRENT: Limite de llamadas concurrentes que usa el semaforo asincrono
    """
    if len(sys.argv) < 2:
        logging.error("Faltan argumentos\n" \
        "Uso: uv run benchmark.py <job_id> <port> <model_name> <total_samples> <max_concurrent>. "
        "Se requiere al menos <job_id>")
        sys.exit(1)

    job_id: str = sys.argv[1]
    port: str = sys.argv[2] if len(sys.argv) > 2 else "8000"
    model_name: str = sys.argv[3] if len(sys.argv) > 3 else "Qwen/Qwen2.5-0.5B-Instruct"
    try:
        total_samples   = int(sys.argv[4]) if len(sys.argv) > 4 else 50
        max_concurrent  = int(sys.argv[5]) if len(sys.argv) > 5 else 5
    except ValueError:
        logging.error("'total_samples' y 'max_concurrent' deben ser numeros enteros")
        sys.exit(1)

    return job_id, port, model_name, total_samples, max_concurrent

async def save_to_jsonl(file_path: Path, record: ExperimentRecord, lock: asyncio.Lock):
    """
    Transforma el registro en texto JSON y lo añade como una nueva linea al final 
    del fichero de resultados del experimento
    """
    async with lock:
        json_line = json.dumps(record.to_dict(), ensure_ascii = False) + "\n"

        def append_line():
            with open(file_path, "a", encoding = "utf-8") as f:
                f.write(json_line)

        #Delegamos la escritura a un hilo para no bloquear el event loop
        await asyncio.to_thread(append_line)

async def process_prompt(row: Dict[str, Any], row_id: int, system_prompt: str, client: LiteLLMClient,
                          sem: asyncio.Semaphore, file_path: Path, file_lock: asyncio.Lock, wandb_table: wandb.Table):
    """
    Prepara los mensajes de una frase, pide la respuesta al servidor, extrae el texto junto a las 
    metricas los tokens y lo manda a guardar
    """
    async with sem:
        logging.info("Procesando fila del dataset con id: %d", row_id)
        user_prompt: str = row["Sentence"]
        messages: ChatPrompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response: ModelResponse | None = await client.send_prompt(messages)
        if response is None:
            logging.warning("Saltando registro por un error en el servidor")
            return

        record: ExperimentRecord = ExperimentRecord.from_response(
            row_id, client.model_name, user_prompt, response
        )
        await save_to_jsonl(file_path, record, file_lock)

        #Añadir la fila a la tabla de W&B
        wandb_table.add_data(
            record.record_id,
            record.input_sentence,
            record.model_output,
            record.usage_metrics.prompt_tokens,
            record.usage_metrics.completion_tokens,
            record.usage_metrics.total_tokens
        )


async def main(dataset_name: str, dataset_split: str, output_dir: Path, system_prompt: str):
    """Orquesta el experimento usando la configuracion dada"""

    #Obtener la configuracion del experimento
    job_id, port, model_name, total_samples, max_concurrent = get_config()

    wandb.init(
        project = "vllm-scaling",
        name = f"{model_name.split('/')[-1]}-concurrent-{max_concurrent}",
        config = {
            "model_name": model_name,
            "total_samples": total_samples,
            "max_concurrent": max_concurrent
        }
    )

    #Tabla de W&B con un ejemplo por fila (prompt, respuesta y tokens)
    results_table = wandb.Table(columns = [
        "ID", "Prompt", "Response", "Prompt Tokens", "Completion Tokens", "Total Tokens"
    ])

    #Preparar y conectar al modelo
    client: LiteLLMClient = LiteLLMClient(
        base_url = f"http://localhost:{port}",
        model = model_name
    )
    if not await client.wait_and_connect():
        return

    #Preparar el directorio y fichero de almacenamiento
    output_dir.mkdir(exist_ok = True)
    output_file : Path = output_dir / f"output_{job_id}.jsonl"

    #Carga del dataset en modo Streaming
    dataset: IterableDataset = load_dataset(dataset_name, split = dataset_split, streaming = True)
    dataset_iterator = iter(dataset)

    #Infraestructura de control de concurrencia y escritura
    sem: asyncio.Semaphore  = asyncio.Semaphore(max_concurrent)
    file_lock: asyncio.Lock = asyncio.Lock()
    tasks = []

    logging.info("Preparando %d prompts en modo streaming asincrono", total_samples)

    for row_id in range(total_samples):
        try:
            row = next(dataset_iterator)
            task = asyncio.create_task(
                process_prompt(row, row_id, system_prompt, client, sem, output_file, file_lock, results_table)
            )
            tasks.append(task)
        except StopIteration: #Dataset sin datos, total_samples < len(dataset)
            break

    logging.info("Tareas creadas. Esperando resolucion con limite de %d llamadas concurrentes",
                max_concurrent)

    await asyncio.gather(*tasks)
    logging.info("Experimento finalizado. Resultados guardados en %s", output_file)

    wandb.log({"evaluation/text_samples": results_table})
    wandb.finish()

if __name__ == "__main__":
    asyncio.run(main(
        dataset_name = DATASET_NAME,
        dataset_split = DATASET_SPLIT,
        output_dir = OUTPUT_DIR,
        system_prompt = SYSTEM_PROMPT
    ))

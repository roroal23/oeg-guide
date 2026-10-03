# pylint: disable=missing-function-docstring

"""
Uso basico de la libreria OpenAI en su modo asincrono frente a un servidor local de vLLM
"""
import logging

import asyncio
from typing import List
from openai import AsyncOpenAI
from openai import APIConnectionError
from openai.types.chat import ChatCompletion

#======= CONFIGURACION =======
MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
DATASET : List[str] = [
    "La capital de Francia es",
    "El teorema de Pitagoras establece que",
    "La computacion de alto rendimiento permite",
    ]
MAX_RETRIES = 15
DELAY = 4.0
#==============================

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

async def wait_and_connect(client: AsyncOpenAI, max_retries: int = 15, delay: float = 2.0) -> bool:
    """
    Realiza un polling al servidor vLLM hasta confirmar que esta activo.
    
    Intenta listar los modelos disponibles usando el cliente de OpenAI.
    Si el servidor aún esta levantando (lo que esperamos dado que el modelo
    corre en local y debe cargar los pesos en memoria), captura el error de
    conexión y reintenta tras un pequeño retardo.

    Returns:
        bool: True si la conexión se estableció
            False si se alcanzó el limite de reintentos sin éxito

    """
    logging.info("Esperando asincronamente a que VLLM responda")
    for attempt in range(1, max_retries + 1):
        try:
            models = await client.models.list()
            model_ids: List[str] = [model.id for model in models.data]
            logging.info("Conectado con exito. Modelos disponibles: %s", model_ids)
            return True
        except APIConnectionError:
            logging.warning("Intento %d/%d. El servidor no responde. Reintentando en %f...",
                            attempt, max_retries, delay)
            await asyncio.sleep(delay)
    logging.error("El servidor vLLM no se activo dentro del tiempo limite establecido")
    return False

async def send_prompt(client:AsyncOpenAI, model:str, prompt:str) -> str:
    try:
        logging.info("Enviando prompt al modelo")
        response : ChatCompletion = await client.chat.completions.create(
            model = model,
            messages = [
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content
        if answer:
            return answer
        else:
            logging.error("Repuesta invalida. Retornando string vacio")
            return ""
    except Exception as e:
        logging.error("Error enviando prompt '%s':\n%s", prompt, e)
        return ""


async def main(model: str, dataset: List[str], max_retries: int, delay: float):
    client: AsyncOpenAI = AsyncOpenAI(
        base_url = "http://localhost:8000/v1",
        api_key = "xxx" #No se necesita API key para usar el servidor local de vLLM
    )

    connected = await wait_and_connect(client, max_retries, delay)
    if not connected:
        return

    tasks = [send_prompt(client, model, prompt) for prompt in dataset]
    responses : List[str] = await asyncio.gather(*tasks)

    for prompt, response in zip(dataset, responses):
        logging.info("Prompt:%s\nRespuesta:%s", prompt, response)


if __name__ == '__main__':
    asyncio.run(main(MODEL, DATASET, MAX_RETRIES, DELAY))

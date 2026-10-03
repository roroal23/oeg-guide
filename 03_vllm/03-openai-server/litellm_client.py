# pylint: disable=missing-function-docstring

"""
Uso basico de la libreria LiteLLM en su modo asincrono frente a un servidor local de vLLM
"""
import logging

import asyncio
from typing import List
from litellm import acompletion
from litellm import ModelResponse
from litellm.exceptions import APIConnectionError


#======= CONFIGURACION =======
BASE_URL = "http://localhost:8000"
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

async def wait_and_connect(
        base_url: str, model: str, max_retries: int = 15, delay: float = 2.0) -> bool:
    """
    Realiza un polling al servidor vLLM hasta confirmar que esta activo.
    
    Si el servidor aún no esta levantando (lo que esperamos dado que el modelo
    corre en local y debe cargar los pesos en memoria), captura el error de
    conexión y reintenta tras un pequeño retardo.

    Returns:
        bool: True si la conexión se estableció
            False si se alcanzó el limite de reintentos sin éxito

    Nota de implementacion:
        LiteLLM no tiene un metodo que lista los modelos disponibles (como teniamos en OpenAI
        o simulabamos con requests). Por ello, nuestro 'heartbeat' pasa a ser una request real al
        modelo con un maximo de 1 token.
    """
    logging.info("Esperando asincronamente a que VLLM responda")
    for attempt in range(1, max_retries + 1):
        try:
            await acompletion(
                model = f"openai/{model}", #vLLM expone una API compatible a la de OpenAI
                api_base = f"{base_url}/v1",
                api_key = "xxx",  #Al ser un servidor local, no se necesita una API KEY
                messages = [
                    {"role":"user", "content":"ping"}
                ],
                max_tokens = 1
            )
            logging.info("Conectado con exito. Modelo disponible: %s", model)
            return True
        except APIConnectionError:
            logging.warning("Intento %d/%d. El servidor no responde. Reintentando en %f...",
                            attempt, max_retries, delay)
            await asyncio.sleep(delay)
    logging.error("El servidor vLLM no se activo dentro del tiempo limite establecido")
    return False

async def send_prompt(base_url: str, model: str, prompt: str) -> str:
    try:
        logging.info("Enviando prompt al modelo")
        response = await acompletion(
            model = f"openai/{model}",
            api_base = f"{base_url}/v1",
            api_key = "xxx",
            messages = [
                {"role": "user", "content": prompt}
            ]
        )
        if not isinstance(response, ModelResponse):
            logging.error("Repuesta invalida. Retornando string vacio")
            return ""

        answer = response.choices[0].message.content
        if answer:
            return answer
        else:
            logging.error("Repuesta invalida. Retornando string vacio")
            return ""
    except Exception as e:
        logging.error("Error enviando prompt '%s':\n%s", prompt, e)
        return ""


async def main(base_url: str, model: str, dataset: List[str], max_retries: int, delay: float):

    connected = await wait_and_connect(base_url, model, max_retries, delay)
    if not connected:
        return

    tasks = [send_prompt(base_url, model, prompt) for prompt in dataset]
    responses : List[str] = await asyncio.gather(*tasks)

    for prompt, response in zip(dataset, responses):
        logging.info("Prompt:%s\nRespuesta:%s", prompt, response)


if __name__ == '__main__':
    asyncio.run(main(BASE_URL, MODEL, DATASET, MAX_RETRIES, DELAY))

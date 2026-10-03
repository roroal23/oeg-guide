# pylint: disable=missing-function-docstring

"""
Uso basico de la libreria requests para comunicarnos con el servidor local de vLLM
"""
import logging

import requests
import time
from typing import List

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


def wait_and_connect(base_url: str, max_retries: int = 15, delay: float = 2.0) -> bool:
    """
    Realiza un polling al servidor vLLM hasta confirmar que esta activo.
    
    Intenta listar los modelos disponibles con una petición GET a /v1/models.
    Si el servidor aún esta levantando (lo que esperamos dado que el modelo
    corre en local y debe cargar los pesos en memoria), captura el error de
    conexión y reintenta tras un pequeño retardo.

    Returns:
        bool: True si la conexión se estableció
            False si se alcanzó el limite de reintentos sin éxito

    """
    logging.info("Esperando a que VLLM responda")
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(f"{base_url}/v1/models", timeout = 5)
            response.raise_for_status()
            model_ids: List[str] = [model["id"] for model in response.json()["data"]]
            logging.info("Conectado con exito. Modelos disponibles: %s", model_ids)
            return True
        except requests.ConnectionError:
            logging.warning("Intento %d/%d. El servidor no responde. Reintentando en %f...",
                            attempt, max_retries, delay)
            time.sleep(delay)
    logging.error("El servidor vLLM no se activo dentro del tiempo limite establecido")
    return False

def send_prompt(base_url: str, model:str, prompt:str) -> str:
    try:
        logging.info("Enviando prompt al modelo")
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json={
                "model": model,
                "messages" : [
                    {"role": "user", "content": prompt}
                ]
            },
            timeout = 60
        )
        answer = response.json()["choices"][0]["message"]["content"]
        if answer:
            return answer
        else:
            logging.error("Repuesta invalida. Retornando string vacio")
            return ""
    except Exception as e:
        logging.error("Error enviando prompt '%s':\n%s", prompt, e)
        return ""

def main(base_url: str, model: str, dataset: List[str], max_retries: int, delay: float):
    connected = wait_and_connect(base_url, max_retries, delay)
    if not connected:
        return

    responses : List[str] = [send_prompt(base_url, model, prompt) for prompt in dataset]

    for prompt, response in zip(dataset, responses):
        logging.info("Prompt:%s\nRespuesta:%s", prompt, response)

if __name__ == '__main__':
    main(BASE_URL, MODEL, DATASET, MAX_RETRIES, DELAY)

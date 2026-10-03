# pylint: disable=missing-function-docstring
"""
Definicion de cliente basado en LiteLLM para interactuar con un servidor local de vLLM
"""

import logging

import asyncio
from typing import List, Dict, Any
from litellm import acompletion
from litellm import ModelResponse
from litellm.exceptions import APIConnectionError, InternalServerError

class LiteLLMClient:
    """
    Cliente asincrono de LiteLLM
    """
    def __init__(self, base_url:str, model:str):
        self.base_url: str = base_url
        self.model_target: str = f"openai/{model}"
        self.model_name: str = model

    async def wait_and_connect(self, max_retries: int = 5, base_delay: float = 2.0) -> bool:
        """
        Realiza un polling asincrono al servidor vLLM usando una petición corta
        como mecanismo de Heartbeat

        Returns:
            True si la conexión se estableció
            False si se alcanzó el limite de reintentos sin éxito
        """
        logging.info("Esperando asincronamente a que VLLM responda")
        for attempt in range(1, max_retries + 1):
            try:
                await acompletion(
                    model = self.model_target,
                    api_base = f"{self.base_url}/v1",
                    api_key = "xxx",  #Al ser un servidor local, no se necesita una API KEY
                    messages = [
                        {"role":"user", "content":"ping"}
                    ],
                    max_tokens = 1,
                    verbosity = "low",
                    num_retries = 0
                )
                logging.info("Conectado con exito. Modelo disponible: %s", self.model_name)
                return True
            except (APIConnectionError, InternalServerError) as e:
                current_delay: float = base_delay * (attempt ** 2)
                logging.warning("Intento %d/%d. El servidor no esta listo (%s). Reintentando en %f",
                                attempt, max_retries, type(e).__name__, current_delay)
                await asyncio.sleep(current_delay)
        logging.error("El servidor vLLM no se activo dentro del tiempo limite establecido")
        return False

    async def send_prompt(self, messages: List[Dict[str, str]],
                          **kwargs: Any) -> ModelResponse | None:
        try:
            logging.info("Enviando prompt al modelo")
            response = await acompletion(
                model = self.model_target,
                api_base = f"{self.base_url}/v1",
                api_key = "xxx",
                messages = messages,
                **kwargs
            )
            if isinstance(response, ModelResponse):
                return response
            return None
        except Exception as e:
            logging.error("Error enviando el conjunto de mensajes:\n%s", e)
            return None

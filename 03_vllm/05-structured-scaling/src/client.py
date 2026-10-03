"""
Definicion de cliente basado en LiteLLM para interactuar con un servidor local de vLLM
"""

import logging

import asyncio
from typing import List, Dict, Any
from litellm import acompletion
from litellm import ModelResponse
import httpx

logger = logging.getLogger("benchmark")

class LiteLLMClient:
    """
    Cliente asincrono de LiteLLM
    """
    def __init__(self, base_url:str, model:str):
        self.base_url: str = base_url
        self.model_name: str = model
        self._model_target: str = f"openai/{model}"
        self._api_base : str = f"{base_url}/v1"
        self._health_url: str = f"{base_url}/health"

    async def wait_and_connect(self, timeout_s: int = 600, interval_s: int = 10) -> bool:
        """
        Polling asincrono al endpoint GET /health de vLLM, cada `interval_s` segundos
        hasta un maximo de `timeout_s` (valores de la seccion global del YAML)
        Returns:
            True si la conexión se estableció
            False si se agotó el tiempo de espera
        """
        max_retries: int = max(1, timeout_s // interval_s)
        logger.info("Verificando disponibilidad del modelo (max %d intentos): %s",
                     max_retries, self._health_url)

        async with httpx.AsyncClient(timeout = httpx.Timeout(5.0)) as client:


            for attempt in range(1, max_retries + 1):
                try:
                    response = await client.get(self._health_url)

                    if response.status_code == 200:
                        logger.info("Conectado con exito. Modelo disponible: %s", self.model_name)
                        return True

                    logger.warning("Intento %d/%d. /health respondio HTTP %d",
                                   attempt, max_retries, response.status_code)

                except httpx.ConnectError as e:
                    logger.warning("Intento %d/%d. Servidor no accesible (%s)",
                                   attempt, max_retries, e)
                except httpx.TimeoutException as e:
                    logger.warning("Intento %d/%d. Timeout en /health (%s)",
                                   attempt, max_retries, e)
                except Exception as e:
                    logger.error("Error inesperado en healthcheck: %s", e)
                    return False

                if attempt < max_retries:
                    await asyncio.sleep(interval_s)

        logger.error("El servidor vLLM no respondio en %d intentos, modelo: %s", 
                      max_retries, self.model_name)
        return False

    async def send_prompt(self, messages: List[Dict[str, str]],
                          **kwargs: Any) -> ModelResponse | None:
        """Envia un conjunto de mensajes al modelo y devuelve la respuesta"""
        try:
            logger.debug("Enviando prompt al modelo")
            response = await acompletion(
                model = self._model_target,
                api_base = self._api_base,
                api_key = "xxx",
                messages = messages,
                **kwargs
            )
            if isinstance(response, ModelResponse):
                return response
            return None
        except Exception as e:
            logger.error("Error en send_prompt:\n%s", e)
            return None

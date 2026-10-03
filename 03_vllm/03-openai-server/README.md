# vLLM como servidor compatible con OpenAI

> Autoría: Rodrigo Najar · Estado: ✅ probado en Magerit (A100) con el stack antiguo; clientes probados en local contra el [servidor falso](../fake_server.py)

## Qué aprendes
- **`vllm serve`** levanta el modelo como un proceso aparte con una API HTTP **compatible con la de OpenAI** (`/v1/models`, `/v1/chat/completions`...). El modelo se queda cargado y cualquier programa puede usarlo.
- Tres formas de hablar con él, de más baja a más alta abstracción:

| Cliente | Estilo | Cómo comprueba que el servidor está listo |
|---|---|---|
| `requests_client.py` | HTTP a mano, síncrono | `GET /v1/models` con reintentos |
| `openai_client.py` | SDK oficial `AsyncOpenAI` | `client.models.list()` |
| `litellm_client.py` | LiteLLM `acompletion` (`model="openai/<nombre>"`) | Una petición de 1 token |

Los tres reintentan mientras el servidor carga los pesos, una idea que el patrón de `/health` de [04](../04-scaling-async) generaliza.

## Cómo ejecutarlo
```bash
sbatch prepare_job.sh
sbatch execute_job.sh     # levanta run_server.sh, espera a /health, lanza los 3 clientes y apaga el servidor
```

En local, sin GPU:
```bash
python3 ../fake_server.py 8000 &
uv run openai_client.py
```

## Notas
- `api_key="xxx"`: el servidor local no comprueba la clave, pero los SDK exigen que se pase alguna.
- `--enforce-eager` desactiva la compilación de *kernels* al arrancar. Arranca antes y rinde algo menos.

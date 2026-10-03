# vLLM en Magerit: lo que aprendimos

[vLLM](https://docs.vllm.ai/) es un motor de inferencia para LLMs que exprime la GPU agrupando peticiones (*continuous batching*) y gestionando la caché de atención por páginas (*PagedAttention*). Este documento recoge lo aprendido en los proyectos de [`03_vllm/`](../03_vllm/), que conviene seguir en orden.

## Dos formas de usarlo

| | Offline: `LLM.generate()` | Servidor: `vllm serve` |
|---|---|---|
| Cómo | El modelo se carga dentro de tu script de Python | Proceso aparte con una API HTTP compatible con la de OpenAI |
| Cuándo | Procesar un lote de prompts de una vez | Varios clientes o programas contra el mismo modelo, o un modelo que se queda cargado |
| Clientes | — | `openai`, `litellm`, `requests`, `curl`... |
| Proyectos | [01-offline](../03_vllm/01-offline), [02-benchmark-wandb](../03_vllm/02-benchmark-wandb) | [03-openai-server](../03_vllm/03-openai-server), [04](../03_vllm/04-scaling-async), [05](../03_vllm/05-structured-scaling) |

## Versiones

Todos los proyectos de vLLM usan:

```toml
requires-python = ">=3.11,<3.12"
dependencies = ["vllm==0.26.0", ...]   # trae torch 2.11 (CUDA 13) y transformers 5.x
```

con el módulo `Python/3.11.3-GCCcore-12.3.0` y **sin** cargar el módulo de CUDA: las wheels de `torch` y vLLM traen su propio runtime de CUDA 13. Si cargas un CUDA del sistema más antiguo, puede confundir a las compilaciones JIT de vLLM.

> [!NOTE]
> **Historia.** Los primeros experimentos del grupo usaron `vllm==0.6.1.post2` + `transformers<4.45` + `setuptools==75.0.0` (torch 2.4 para CUDA 12.1, módulo `CUDA/12.1.1`), que funcionaba también en V100 con `dtype="half"`. Al pasar a proyectos más serios actualizamos a vLLM 0.2x. Si necesitas trabajar en una V100, vuelve a ese stack antiguo.

**Cambios que nos encontramos al actualizar desde 0.6:**
- `--guided-decoding-backend` ya no existe. Ahora es `--structured-outputs-config.backend <backend>`, y solo hace falta si usas salidas estructuradas (JSON, regex...).
- `--disable-log-requests` ya no existe: el log de peticiones viene desactivado por defecto (`--enable-log-requests` lo activa).
- vLLM compila *kernels* al arrancar (`torch.compile`/Triton), así que necesita `gcc` en el nodo. Por eso el primer arranque tarda más, y `--enforce-eager` lo evita a costa de rendimiento.
- La API de Python (`LLM`, `SamplingParams`, `RequestOutput`) sigue igual en lo que usamos.

## GPUs: A100, V100 y bfloat16

Los modelos Qwen2.5 usan por defecto `bfloat16`, que requiere *compute capability* ≥ 8.0 (A100 sí, V100 no). Con el stack antiguo, la V100 daba este error:

```
ValueError: Bfloat16 is only supported on GPUs with compute capability of at least 8.0.
Your Tesla V100-PCIE-16GB GPU has compute capability 7.0. You can use float16 instead
by explicitly setting the `dtype` flag in CLI, for example: --dtype=half.
```

Además, `torch` 2.11 está compilado para CUDA 13, que ya no da soporte a la arquitectura Volta de la V100. Por eso **todos los proyectos de `03_vllm` piden una A100** (`#SBATCH --gres=gpu:a100:1`).

Para modelos de 7B, una A100 y `--mem=48G` son suficientes. Con 16 GB de RAM el 7B no llegaba a cargar.

## Servidor + cliente en el mismo trabajo

El patrón de [`templates/server_client_job.sh`](../templates/server_client_job.sh) tiene cuatro pasos:

1. Lanzar `uv run vllm serve ... &` en segundo plano y guardar su PID.
2. **Esperar activamente** a que `GET /health` responda 200, con un timeout. Hay que comprobar además que el proceso sigue vivo, porque si vLLM muere al cargar no tiene sentido esperar el timeout entero. Cargar los pesos tarda desde unos segundos hasta varios minutos según el modelo; un `sleep 300` fijo o se queda corto o desperdicia GPU.
3. Lanzar el cliente y guardar su código de salida.
4. `kill` del servidor y `exit` con el código del cliente, para que SLURM marque el trabajo como fallido si el cliente falló.

## Clientes asíncronos y concurrencia

Un cliente secuencial (pregunta, espera la respuesta, siguiente pregunta) deja la GPU infrautilizada: vLLM rinde más cuantas más peticiones atiende a la vez. En [04-scaling-async](../03_vllm/04-scaling-async) se usa `asyncio`:

- **`asyncio.Semaphore(N)`** limita las peticiones simultáneas a N. Conviene que coincida con `--max-num-seqs` del servidor.
- **El dataset se lee en *streaming*** (`load_dataset(..., streaming=True)`), así que no se carga entero en memoria.
- **Escritura de resultados:** en la v1, cada tarea abre el fichero bajo un `asyncio.Lock`. En [05-structured-scaling](../03_vllm/05-structured-scaling), un único *writer* consume de una `asyncio.Queue` acotada (patrón productor-consumidor).

¿Por qué `asyncio` y no hilos ni procesos? Mientras se espera la respuesta HTTP, el programa no usa CPU: es trabajo de E/S, y ahí `asyncio` es ideal. Para trabajo de CPU es al revés; míralo en [01_fundamentals/concurrency-and-parallelism](../01_fundamentals/concurrency-and-parallelism).

## Caché de modelos

Los pesos se descargan de Hugging Face la primera vez y se guardan en `HF_HOME`. En Magerit apúntalo a `PROJECT`, que es compartido entre los miembros del proyecto y tiene más cuota:

```bash
export HF_HOME="$(dirname "$HOME")/PROJECT/.cache/huggingface"
```

Cuidado con la sintaxis de bash: `export HF_HOME = "..."`, con espacios alrededor del `=`, **es un error** y la variable no se define. Nos pasó.

## Probar sin GPU

[`03_vllm/fake_server.py`](../03_vllm/fake_server.py) imita `/health`, `/v1/models` y `/v1/chat/completions` y solo usa la librería estándar. Con él puedes ejecutar en tu PC los clientes de 03, 04 y 05 y comprobar que la lógica asíncrona, la escritura del JSONL y W&B (con `WANDB_MODE=offline`) funcionan antes de gastar horas de GPU.

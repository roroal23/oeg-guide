# 03 · vLLM

Proyectos para servir LLMs con [vLLM](https://docs.vllm.ai/) en Magerit. Están pensados para seguirse **en orden**: cada uno añade una idea sobre el anterior. La teoría y los problemas que nos encontramos están en [docs/04-vllm-on-magerit.md](../docs/04-vllm-on-magerit.md).

| # | Proyecto | Idea nueva | Autoría |
|---|---|---|---|
| 1 | [01-offline](01-offline) | `LLM.generate()`: estructura de las salidas y parámetros de muestreo | Rodrigo |
| 2 | [02-benchmark-wandb](02-benchmark-wandb) | Dataset de Hugging Face, varios modelos en un trabajo y registro en W&B | Shuyi |
| 3 | [03-openai-server](03-openai-server) | `vllm serve` y tres clientes (requests, OpenAI, LiteLLM) | Rodrigo |
| 4 | [04-scaling-async](04-scaling-async) | Cliente asíncrono con semáforo, dataset en *streaming*, JSONL y W&B | Rodrigo y Shuyi |
| 5 | [05-structured-scaling](05-structured-scaling) | Configuración en YAML con Pydantic, *writer* productor-consumidor, métricas por petición | Rodrigo y Shuyi |

Todos usan el mismo stack (Python 3.11, `vllm==0.26.0`) y una **A100**. En cada carpeta:

```bash
sbatch prepare_job.sh     # una vez: uv sync en la partición debug
sbatch execute_job.sh     # ver la cabecera del script para los argumentos
```

## Probar sin GPU
[`fake_server.py`](fake_server.py) imita la API de `vllm serve` (`/health`, `/v1/models` y `/v1/chat/completions`) con la librería estándar. Sirve para probar en tu PC los clientes de 03, 04 y 05:

```bash
python3 fake_server.py 8000 &
cd 04-scaling-async
WANDB_MODE=offline uv run benchmark.py local 8000 Qwen/Qwen2.5-0.5B-Instruct 10 4
```

## W&B en Magerit
Los proyectos 02, 04 y 05 registran resultados en [Weights & Biases](https://wandb.ai). Haz login una vez en Magerit (la clave se guarda en `~/.netrc`, nunca en el repo):

```bash
uv run wandb login
```

Para probar sin subir nada, usa `WANDB_MODE=offline`.

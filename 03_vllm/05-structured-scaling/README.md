# Benchmark asíncrono, versión estructurada

> Autoría: Rodrigo Najar y Shuyi · Estado: ✅ probado en local contra el [servidor falso](../fake_server.py); pendiente de ejecutar en Magerit

## Qué aprendes
El mismo experimento que [04-scaling-async](../04-scaling-async), organizado como un proyecto «de verdad»:

| Módulo (`src/`) | Responsabilidad |
|---|---|
| `config.py` | Configuración en **YAML validada con Pydantic** (`global` + lista de `models`, cada uno con sus parámetros de vLLM). También tiene un pequeño CLI para que bash lea el YAML. |
| `benchmark.py` | Orquestación: argumentos (`argparse`), productores asíncronos con semáforo y resumen final. |
| `client.py` | Cliente LiteLLM; espera a `GET /health` (con `httpx`). |
| `writer.py` | **Productor-consumidor**: un único *writer* lee de una `asyncio.Queue` acotada y escribe el JSONL. |
| `wandb_logger.py` | Otro consumidor que envía a W&B las métricas de cada petición (latencia, tokens), una tabla de ejemplos y un resumen (*throughput*, latencia media, errores). |
| `structures.py` | Registros validados con Pydantic. |
| `logging_setup.py` | Logger con `[job=... model=...]` en cada línea. |

**El YAML es la única fuente de verdad.** `execute_job.sh` lee de él el puerto y los flags de `vllm serve`:
```bash
uv run python -m src.config --yaml config.example.yaml --model Qwen/Qwen2.5-7B-Instruct --vllm-args
# --dtype bfloat16 --max-model-len 4096 --max-num-seqs 10 --gpu-memory-utilization 0.9
```

## Cómo ejecutarlo
```bash
cp config.example.yaml config.yaml        # ajústalo
uv run wandb login                        # una vez
sbatch prepare_job.sh
sbatch execute_job.sh Qwen/Qwen2.5-7B-Instruct config.yaml
```

En local, contra el servidor falso:
```bash
python3 ../fake_server.py 8000 &
WANDB_MODE=offline uv run python -m src.benchmark --yaml config.example.yaml \
    --model Qwen/Qwen2.5-0.5B-Instruct --job-id local
```

## Qué deberías ver
`outputs/output_<job_id>_<modelo>.jsonl` y, al final del log:
```
Experimento finalizado. Completados: 50, errores: 0, tokens promedio: ..., latencia promedio: ...s, throughput: .../min
```

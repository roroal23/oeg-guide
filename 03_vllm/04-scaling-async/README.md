# Benchmark asíncrono contra vLLM

> Autoría: Rodrigo Najar y Shuyi · Estado: ✅ probado en Magerit (A100) con el stack antiguo; probado en local contra el [servidor falso](../fake_server.py)

## Qué aprendes
Cómo mandar **miles de peticiones** a un servidor vLLM sin saturarlo ni dejar la GPU ociosa:

- **`asyncio` + `Semaphore(N)`**: hasta N peticiones en vuelo a la vez (`benchmark.py: process_prompt`). Conviene que N coincida con `--max-num-seqs` del servidor.
- **Dataset en *streaming*** (`load_dataset(..., streaming=True)`): EsCoLA no se carga entero en memoria.
- **Resultados validados** con `dataclasses` (`structures.py`) y guardados en **JSONL** (una línea por petición, con tokens de entrada y salida).
- **E/S sin bloquear el *event loop***: la escritura se delega a un hilo (`asyncio.to_thread`) y se protege con un `asyncio.Lock`.
- **W&B**: un *run* por configuración (`<modelo>-concurrent-<N>`) con una tabla de ejemplos.
- **`execute_job.sh`**: el patrón completo de servidor + espera activa sobre `/health` + cliente + limpieza.

Es una mejora directa de [03-openai-server](../03-openai-server). La versión [05](../05-structured-scaling) reorganiza el mismo experimento con configuración YAML y un *writer* único.

## Cómo ejecutarlo
```bash
uv run wandb login                                          # una vez
sbatch prepare_job.sh
sbatch execute_job.sh                                       # 5 concurrentes, Qwen2.5-0.5B, 9500 frases
sbatch execute_job.sh 10 Qwen/Qwen2.5-7B-Instruct 9500      # MAX_CONCURRENT MODELO TOTAL_SAMPLES
```

Directamente (con un servidor ya levantado):
```bash
uv run benchmark.py <job_id> <puerto> <modelo> <total_samples> <max_concurrent>
```

## Qué deberías ver
`outputs/output_<job_id>.jsonl`, con un registro como este por frase:
```json
{"record_id": 3, "timestamp": "...", "model": "Qwen/Qwen2.5-0.5B-Instruct",
 "input_sentence": "Sólo tenía una peseta, y aquel tipo me pedía doscientos.",
 "model_output": "Correcta. ...", "usage_metrics": {"prompt_tokens": 47, "completion_tokens": 6, "total_tokens": 53}}
```
Comparar varios valores de `MAX_CONCURRENT` en W&B muestra cómo escala el rendimiento.

## Limitaciones
- Cada petición abre el fichero de salida para escribir una línea. La versión 05 lo resuelve con un único *writer* que consume de una cola.
- Si una petición falla, se registra en el log y se salta; no se reintenta.

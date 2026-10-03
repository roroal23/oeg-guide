# Benchmark offline con Weights & Biases

> Autoría: Shuyi · Estado: ✅ probado en Magerit con el stack antiguo (V100 y A100); pendiente de validar con vLLM 0.26

## Qué aprendes
- Cargar un dataset de Hugging Face (`nbel/EsCoLA`, 50 frases) y pasarlo a vLLM en bloque.
- Probar **varios modelos** (Qwen2.5 0.5B/1.5B/3B/7B) uno tras otro en un mismo trabajo de SLURM.
- Registrar resultados en **W&B**: un *run* por modelo, una tabla prompt/respuesta y las métricas del sistema.

| Script | Qué registra en W&B |
|---|---|
| `benchmark.py <modelo> [proyecto]` | Tabla prompt → respuesta |
| `benchmark_speed.py <modelo>` | Además: tiempo de generación, tokens/s y nº de prompts (ver `utilities.py`) |

## Cómo ejecutarlo
```bash
uv run wandb login                                   # una vez
sbatch prepare_job.sh
sbatch execute_job.sh                                # benchmark.py con 0.5B, 1.5B y 3B
sbatch execute_job.sh benchmark_speed.py
sbatch execute_job.sh benchmark.py Qwen/Qwen2.5-7B-Instruct
```

## Qué mirar en W&B: la pestaña *System*
W&B registra automáticamente unas 20 métricas de sistema. Las más útiles para un benchmark de inferencia son estas:

1. **GPU Memory Allocated (bytes / %).** Cuánto ocupan los pesos más la caché KV. vLLM reserva por defecto el 90 % de la memoria (`gpu_memory_utilization`), así que suele verse alto.
2. **GPU Time Spent Accessing Memory (%).** Generar cada token obliga a leer todos los pesos desde la VRAM. Un valor alto indica que el cuello de botella es el ancho de banda de memoria (lo normal en inferencia) y no el cálculo.
3. **GPU Utilization (%).** Si vLLM mantiene la GPU «alimentada». Lo ideal es acercarse al 100 %.
4. **Process Memory In Use (MB) / System Memory Utilization (%).** RAM de CPU. Al cargar el 7B con 16 GB de RAM nos quedamos cortos.
5. **GPU Power Usage (W) y GPU Temperature (°C).** Uso físico de la tarjeta. Cerca de 85–90 °C la GPU baja frecuencias para protegerse.

Otras métricas que también aparecen:
- *GPU Corrected/Uncorrected Memory Errors:* errores de VRAM; si suben, el hardware se degrada.
- *SM/Memory Clock Speed:* frecuencias de cálculo y de memoria.
- *Enforced Power Limit:* tope de vatios.
- *Network Traffic:* subida a W&B y descarga de pesos.
- *Disk I/O:* lecturas del sistema de ficheros BeeGFS de Magerit.

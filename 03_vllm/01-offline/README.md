# vLLM offline: `LLM.generate()`

> Autoría: Rodrigo Najar · Estado: ✅ probado en Magerit con el stack antiguo; pendiente de validar con vLLM 0.26

## Qué aprendes
El modo más simple de vLLM: el modelo se carga **dentro de tu script** y procesa un lote de prompts de una vez.

- **`vllm_inspector.py`** imprime el objeto `RequestOutput` tal cual y después desglosado: `request_id`, `prompt`, `outputs[i].text` y `metrics`. Así ves qué devuelve vLLM.
- **`sampling_params.py`** lanza los mismos prompts con 5 perfiles de `SamplingParams` y compara cómo cambia el texto:

| Perfil | Parámetros | Efecto |
|---|---|---|
| estable | `temperature=0` | Determinista |
| creativo | `temperature=0.8, top_p=0.9, frequency_penalty=0.2` | Más variado, recorta lo improbable |
| variado controlado | `temperature=1.0, min_p=0.05` | Variado, salvo cuando el modelo duda |
| anti repeticiones | `repetition_penalty=1.2, presence_penalty=0.4` | Evita bucles |
| brainstorming | `temperature=1.5, top_k=50, top_p=0.85` | Máxima variedad |

## Requisitos
GPU A100 en Magerit (ver [docs/04](../../docs/04-vllm-on-magerit.md)). Modelo: `Qwen/Qwen2.5-0.5B-Instruct`.

## Cómo ejecutarlo
```bash
sbatch prepare_job.sh
sbatch execute_job.sh                       # vllm_inspector.py
sbatch execute_job.sh sampling_params.py
```

## Limitaciones
`RequestOutput.metrics` cambia de tipo entre versiones de vLLM y puede venir vacío.

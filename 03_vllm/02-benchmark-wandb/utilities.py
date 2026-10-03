import time
import wandb
from typing import List
from vllm import LLM, SamplingParams

def run_experiment(llm: LLM, prompts: List[str], sampling_params: SamplingParams):
    # 1. Medir el tiempo antes de generar
    start = time.perf_counter()
    
    # 2. Generar las respuestas
    outputs = llm.generate(prompts, sampling_params)
    
    # 3. Medir el tiempo al terminar
    end = time.perf_counter()
    total_time = end - start
    
    # 4. Calcular los tokens totales y la velocidad
    total_tokens = sum(len(output.outputs[0].token_ids) for output in outputs)
    tokens_per_second = total_tokens / total_time if total_time > 0 else 0
    
    # 5. Crear una tabla de W&B con las columnas que queremos
    text_table = wandb.Table(columns=["Prompt", "Generated Text"])
    
    # 6. Recorrer las salidas y añadir cada par a la tabla
    for output in outputs:
        original_prompt = output.prompt
        generated_text = output.outputs[0].text
        text_table.add_data(original_prompt, generated_text)
    
    # 7. Subir todo (métricas numéricas + tabla de textos) a W&B
    wandb.log({
        "evaluation/generation_time_s": total_time,
        "evaluation/tokens_per_second": tokens_per_second,
        "evaluation/total_prompts": len(prompts),
        "evaluation/text_samples": text_table  # <-- Subida de la tabla
    })

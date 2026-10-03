"""
benchmark_speed.py
Igual que benchmark.py, pero además mide el tiempo de generación y los tokens/s
(ver utilities.run_experiment) y los registra como métricas en W&B.
Uso: uv run benchmark_speed.py <modelo_hf>
"""
import sys
import wandb
from vllm import LLM, SamplingParams
from datasets import load_dataset
from utilities import run_experiment

MAX_TOKENS = 50

def main():
    # 1. Leer el modelo desde los argumentos al ejecutar el script
    if len(sys.argv) < 2:
        print("Error: Debes proporcionar el nombre del modelo.")
        sys.exit(1)

    model_name = sys.argv[1]
    run_name = model_name.split("/")[-1]

    dataset = load_dataset("nbel/EsCoLA", split="train[:50]")
    prompts = dataset['Sentence'] # Columna que contiene las oraciones

    # 2. Inicializar W&B. Cada vez que se ejecute el script, creará una nueva línea
    wandb.init(project="escola-benchmark3", name=run_name, config={"model": model_name, "max_tokens": MAX_TOKENS})

    # 3. Iniciar vLLM (cargará el modelo en la GPU))
    llm = LLM(model=model_name)
    sampling_params = SamplingParams(max_tokens=MAX_TOKENS)

    # 4. Ejecutar el experimento
    run_experiment(llm, prompts, sampling_params)

    wandb.finish()
    print("Experimento finalizado.")

if __name__ == '__main__':
    main()

"""
benchmark.py
Genera respuestas con vLLM (modo offline) para las 50 primeras frases de EsCoLA
y sube una tabla prompt/respuesta a Weights & Biases.
Uso: uv run benchmark.py <modelo_hf> [proyecto_wandb]
"""
import sys
import wandb
from datasets import load_dataset
from vllm import LLM, SamplingParams

def main():
    # 1. Leer el modelo (y opcionalmente el proyecto de W&B) desde los argumentos
    if len(sys.argv) < 2:
        print("Uso: uv run benchmark.py <modelo_hf> [proyecto_wandb]")
        sys.exit(1)

    model_name = sys.argv[1]
    project = sys.argv[2] if len(sys.argv) > 2 else "escola-benchmark"
    run_name = model_name.split("/")[-1]

    # 2. Inicializar W&B. Cada ejecución crea un nuevo "run" dentro del proyecto
    wandb.init(project=project, name=run_name, config={"model": model_name})

    # 3. Cargar el dataset EsCoLA
    print(f"Cargando dataset y evaluando el modelo {model_name}...")
    dataset = load_dataset("nbel/EsCoLA", split="train[:50]")
    prompts = dataset['Sentence'] # Columna que contiene las oraciones

    # 4. Iniciar vLLM (carga el modelo en la GPU))
    llm = LLM(model=model_name)
    sampling_params = SamplingParams(max_tokens=50)

    # 5. Generar respuestas en bloque
    outputs = llm.generate(prompts, sampling_params)

    # 6. Guardar los resultados en una tabla de W&B
    results_table = wandb.Table(columns=["Prompt", "Generated Text"])

    for output in outputs:
        prompt = output.prompt
        generated_text = output.outputs[0].text
        results_table.add_data(prompt, generated_text)

    wandb.log({"escola_samples": results_table})
    wandb.finish()
    print(f"Benchmark del modelo {model_name} completado.")

if __name__ == '__main__':
    main()

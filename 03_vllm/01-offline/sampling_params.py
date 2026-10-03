# pylint: disable=missing-function-docstring

"""
sampling_params.py:
Probamos un mismo modelo frente a una serie de prompts pero en cada ocasion variamos los
Parametros de Muestreo. De esta forma, 'controlamos' como responde el LLM a los prompts.
"""

from vllm import LLM, SamplingParams
from typing import List, Dict

from utilities import run_experiment


#======= CONFIGURACION =======
MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
DATASET : List[str] = [
    "El proposito de la inteligencia artificial es",
    "Una frase creativa sobre los planetas es:"
    ]
MAX_TOKENS = 50
#==============================



def main(model: str, dataset: List[str], max_tokens: int):
    llm : LLM = LLM(model = model)

    #Variaciones de parametros
    sampling_profiles: Dict[str, SamplingParams] = {
        #Sin creatividad (determinista), considera todas las palabras. El mas estable
        "estable":  SamplingParams(
            temperature = 0.0, top_p = 1.0, presence_penalty = 0.0, max_tokens = max_tokens
        ),
        #Alta creatividad, recorta palabras con poca probabilidad, penaliza repeticion
        "creativo": SamplingParams(
            temperature = 0.8, top_p = 0.9, frequency_penalty = 0.2, max_tokens = max_tokens
        ),
        #Alta creatividad, pero limita palabras cuando el modelo no esta seguro
        "variado controlado": SamplingParams(
            temperature = 1.0, min_p = 0.05, max_tokens = max_tokens
        ),
        #Penaliza la repetición. Util para listas o cuando el modelo entra en bucle
        "anti repeticiones": SamplingParams(
            repetition_penalty = 1.2, presence_penalty = 0.4, max_tokens = max_tokens
        ),
        #Maxima variedad, se permite todo pero escoge las 50 mejores opciones
        "brainstorming": SamplingParams(
            temperature = 1.5, top_k = 50, top_p = 0.85, max_tokens = max_tokens
        )
    }

    for profile, params in sampling_profiles.items():
        print(f"=== EXPERIMENTO CON MODELO ESTILO : {profile} ===")
        run_experiment(llm, dataset, params)


if __name__ == '__main__':
    main(MODEL, DATASET, MAX_TOKENS)

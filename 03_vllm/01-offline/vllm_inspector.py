# pylint: disable=missing-function-docstring

"""
vllm_inspector.py
Uso basico de vLLM para inspeccionar la estructura de los objetos que devuelve
"""

from vllm import LLM, SamplingParams
from typing import List

from utilities import print_full_responses

#======= CONFIGURACION =======
MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
DATASET : List[str] = [
    "La capital de Francia es",
    "El teorema de Pitagoras establece que",
    "La computacion de alto rendimiento permite",
    ]
#==============================

def main(model: str, dataset : List[str]):

    llm : LLM = LLM(model = model)
    sampling_params : SamplingParams = SamplingParams(
        temperature = 0, max_tokens = 256
    )

    outputs = llm.generate(dataset, sampling_params)

    print("====== OBJETO PLANO =======") #Visualizar el objeto plano
    print(outputs)
    print("===== RESPUESTAS DESGLOSADAS ====")
    print_full_responses(outputs)#Visualizar desglose de campos


if __name__ == '__main__':
    main(MODEL, DATASET)

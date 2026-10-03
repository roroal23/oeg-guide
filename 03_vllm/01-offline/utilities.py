# pylint: disable=missing-function-docstring

"""
utilities.py:
Modulo que contiene metodos comunes para las pruebas con vllm
"""

from vllm import LLM, SamplingParams
from vllm.outputs import RequestOutput, CompletionOutput

from typing import List


def run_experiment(llm: LLM, prompts: List[str], sampling_params: SamplingParams):
    outputs = llm.generate(prompts, sampling_params)
    print_responses(outputs)

def print_full_responses(request_outputs: List[RequestOutput]):
    for request_output in request_outputs:
        print("== RESPUESTA ==")
        request_id: str = request_output.request_id
        print(f"Id: {request_id}")

        #Prompt enviado
        if request_output.prompt:
            prompt: str = request_output.prompt
            print(f"Prompt: {prompt}")
        else:
            print("Prompt: [No hay prompt]")

        #Lista de respuestas
        outputs: List[CompletionOutput] = request_output.outputs
        for output in outputs:
            n_output = output.index
            response_str = output.text
            print(f"Respuesta {n_output}:\n{response_str}")

        #Metricas
        # (el tipo de este objeto cambia entre versiones de vLLM y puede ser None)
        if request_output.metrics:
            metrics = request_output.metrics
            print(f"Metricas:\n{metrics}")
        else:
            print("Metricas: [No hay metricas]")


def print_responses(request_outputs: List[RequestOutput]):
    for request_output in request_outputs:
        print("== RESPUESTA ==")

        #Prompt enviado
        if request_output.prompt:
            prompt: str = request_output.prompt
            print(f"Prompt: {prompt}")
        else:
            print("Prompt: [No hay prompt]")

        #Lista de respuestas
        outputs: List[CompletionOutput] = request_output.outputs
        for output in outputs:
            n_output = output.index
            response_str = output.text
            print(f"Respuesta {n_output}:\n{response_str}")

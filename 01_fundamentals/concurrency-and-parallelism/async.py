# pylint: disable=missing-function-docstring

"""
async.py
Version del trabajo de alta carga de CPU con metodos asincronos
"""

import asyncio
from time import perf_counter
from typing import List
from primes import PrimeResult, check, NUMBERS

async def check_async(n: int) -> PrimeResult:
    #Wrapper asincrono de check(n)
    return check(n)

async def evaluate(numbers: List[int]) -> List[PrimeResult]:
    #Lista de tareas
    tasks = [check_async(n) for n in numbers]
    #asyncio.gather lanza las tareas y espera a que todas terminen
    return await asyncio.gather(*tasks)

def report(results: List[PrimeResult]) -> int:
    checked = 0
    for n, is_prime, duration in results:
        label = 'P' if is_prime else ' '
        print(f"{n}    {label} {duration:9.6f}s")
        checked += 1
    return checked

async def main_async(numbers_to_check: List[int]):
    print(f"Iniciando la evaluacion de {len(numbers_to_check)} numeros...")

    initial_time = perf_counter()

    results = await evaluate(numbers_to_check)

    checked = report(results)
    total_duration = perf_counter() - initial_time
    print(f"Evaluados {checked} numeros en {total_duration:.2f}s")

if __name__ == '__main__':
    #Lanzamos el bucle de eventos
    asyncio.run(main_async(NUMBERS))

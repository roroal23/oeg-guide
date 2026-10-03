# pylint: disable=missing-function-docstring

"""
sequential.py:
Base para comparar ejecuciones secuenciales, con hilos, con procesos y asincronas
para trabajos de alta carga de CPU
"""

from time import perf_counter
from typing import List

from primes import PrimeResult, check, NUMBERS

def report(results: List[PrimeResult]) -> int:
    checked = 0
    for n, is_prime, duration in results:
        label = 'P' if is_prime else ' '
        print(f"{n}    {label} {duration:9.6f}s")
        checked += 1
    return checked

def evaluate(numbers: List[int]) -> List[PrimeResult]:
    return [check(n) for n in numbers]

def main(numbers_to_check: List[int]):
    print(f"Iniciando la evaluacion de {len(numbers_to_check)} numeros...")
    initial_time = perf_counter()

    results = evaluate(numbers_to_check)

    checked = report(results)
    total_duration = perf_counter() - initial_time
    print(f"Evaluados {checked} numeros en {total_duration:.2f}s")

if __name__ == '__main__':
    main(NUMBERS)

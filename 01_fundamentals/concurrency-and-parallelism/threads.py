# pylint: disable=missing-function-docstring

"""
threads.py
Version del trabajo de alta carga de CPU con hilos
"""

import sys
from time import perf_counter
from queue import SimpleQueue
from threading import Thread
from typing import List
from os import cpu_count

from primes import PrimeResult, check, NUMBERS

JobQueue    = SimpleQueue
ResultQueue = SimpleQueue

def worker(jobs: JobQueue, results: ResultQueue) -> None:
    while n := jobs.get():
        results.put(check(n))
    #"Poison pill", marcador de que el proceso ha finalizado
    results.put(PrimeResult(0, False, 0.0))

def start_jobs(n_threads: int, numbers: List[int], jobs: JobQueue, results: ResultQueue) -> None:
    for n in numbers:
        jobs.put(n)
    for _ in range(n_threads):
        thread = Thread(target = worker, args = (jobs, results))
        thread.start()
        #Coloca un 0 en la cola por cada hilo lanzado para marcar que debe finalizar
        jobs.put(0)

def report(n_threads: int, results: ResultQueue) -> int:
    checked = 0
    threads_done = 0
    while threads_done < n_threads:
        n, is_prime, duration = results.get()
        if n == 0:
            threads_done += 1
        else:
            checked += 1
            label = 'P' if is_prime else ' '
            print(f"{n}    {label} {duration:9.6f}s")
    return checked

def main(numbers_to_check: List[int]):
    if len(sys.argv) < 2:
        n_threads = cpu_count() or 1
    else:
        n_threads = int(sys.argv[1])
    print(f"Iniciando la evaluacion de {len(numbers_to_check)} numeros...")

    jobs: JobQueue = SimpleQueue()
    results: ResultQueue = SimpleQueue()
    initial_time = perf_counter()

    start_jobs(n_threads, numbers_to_check, jobs, results)

    checked = report(n_threads, results)
    total_duration = perf_counter() - initial_time
    print(f"Evaluados {checked} numeros en {total_duration:.2f}s")

if __name__ == '__main__':
    main(NUMBERS)

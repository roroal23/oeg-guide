"""
primes.py:
Modulo que contiene utilidades para realizar pruebas de primalidad
"""

from time import perf_counter
from typing import NamedTuple
import math


NUMBERS : list[int] = [299593572317531] * 18

class PrimeResult(NamedTuple):
    """
        Resultado de una unica prueba de primalidad.
    """
    number: int
    prime: bool
    elapsed: float

def is_prime(n: int) -> bool:
    """
        Prueba de primalidad basica
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    root = math.isqrt(n)
    for i in range(3, root + 1, 2):
        if n % i == 0:
            return False
    return True

def check(n: int) -> PrimeResult:
    """
        Ejecuta una prueba de primalidad, contando el tiempo que tarda.
    """
    t0 = perf_counter()
    prime = is_prime(n)
    return PrimeResult(n, prime, perf_counter() - t0)

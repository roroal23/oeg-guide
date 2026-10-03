# Concurrencia y paralelismo en Python

> Autoría: Rodrigo Najar · Estado: ✅ funciona (CPU)

## Qué aprendes
El mismo trabajo CPU-bound (comprobar si 18 números grandes son primos) implementado de cuatro formas: **secuencial, con hilos, con procesos y con `asyncio`**. Sirve para ver en la práctica el efecto del **GIL**, y es la base para entender por qué los clientes de vLLM usan `asyncio`, un trabajo de E/S, y no procesos.

| Fichero | Estrategia |
|---|---|
| `primes.py` | Test de primalidad común y la lista `NUMBERS` |
| `sequential.py` | Uno detrás de otro |
| `threads.py` | Un hilo por núcleo, con colas y una *poison pill* para terminar |
| `processes.py` | Un proceso por núcleo, con el mismo esquema de colas |
| `async.py` | Corrutinas con `asyncio.gather` |

## Requisitos
Python 3.12 y [uv](../../docs/02-uv.md). Solo usa la librería estándar.

## Cómo ejecutarlo
```bash
bash compare.sh                 # las cuatro versiones seguidas
uv run processes.py 4           # procesos/hilos aceptan el nº de workers
```

## Qué deberías ver
En un portátil con 8 núcleos:

| Versión | Tiempo |
|---|---|
| Secuencial | 5,6 s |
| Procesos | **1,8 s** |
| Hilos | 5,6 s |
| asyncio | 5,2 s |

- **Hilos ≈ secuencial:** por el GIL, solo un hilo ejecuta bytecode de Python a la vez, así que en trabajo de CPU los hilos no aceleran.
- **Procesos:** cada proceso tiene su propio intérprete y su propio GIL, así que sí hay paralelismo real.
- **`asyncio` ≈ secuencial:** las corrutinas no ceden el control mientras calculan. `asyncio` brilla cuando el programa *espera* (red, disco), como en los clientes de [`03_vllm`](../../03_vllm).

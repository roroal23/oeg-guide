# Plantillas

Scripts para trabajar en Magerit con [uv](../docs/02-uv.md) y SLURM. Todas siguen las mismas convenciones:

- **Sin `--chdir`.** SLURM ejecuta el trabajo en el directorio desde el que lanzas `sbatch`, así que **lanza siempre `sbatch` desde la carpeta del proyecto**.
- **Logs en `logs/`.** La carpeta tiene que existir antes de lanzar el trabajo; si no, SLURM no puede crear el fichero de log y el trabajo falla sin decir nada. Los proyectos la versionan con un `logs/.gitkeep`.
- **Cachés fuera del `$HOME`.** `UV_CACHE_DIR` y `HF_HOME` apuntan a `/home/<code>/PROJECT/.cache/`, porque los modelos de Hugging Face no caben en la cuota personal.
- **Líneas marcadas con `CONFIGURA`.** Son las que tienes que editar: tu correo y el módulo de Python, que debe coincidir con el `.python-version` del proyecto.

| Fichero | Para qué sirve |
|---|---|
| [`init_project.sh`](init_project.sh) | Crea un proyecto uv nuevo con `logs/`, `prepare_job.sh` y `execute_job.sh` ya configurados. |
| [`prepare_job.sh`](prepare_job.sh) | Ejecuta `uv sync` en la partición `debug` (sin GPU) para instalar el entorno. Se lanza una vez, y de nuevo cada vez que cambien las dependencias. |
| [`execute_job.sh`](execute_job.sh) | Ejecuta `uv run main.py` en una GPU y reenvía los argumentos de `sbatch`. |
| [`server_client_job.sh`](server_client_job.sh) | Levanta un servidor vLLM, espera a `/health`, lanza un cliente y apaga el servidor. Es el patrón de [`03_vllm/04-scaling-async`](../03_vllm/04-scaling-async). |
| [`PROJECT_README_TEMPLATE.md`](PROJECT_README_TEMPLATE.md) | Esqueleto de README para cada proyecto nuevo. |
| [`slurm-cheatsheet.md`](slurm-cheatsheet.md) | Los comandos de uso diario. |

## Flujo típico

```bash
source templates/init_project.sh
init_project mi_experimento nombre.apellido@alumnos.upm.es 3.12
cd mi_experimento
uv add torch transformers        # en local: actualiza pyproject.toml y uv.lock
# ... escribir main.py, probar en local, subir a Magerit (git o scp) ...
sbatch prepare_job.sh            # en Magerit
sbatch execute_job.sh
squeue --me
```

> [!TIP]
> ¿Por qué hay dos trabajos? `prepare_job.sh` descarga e instala paquetes, algo que no necesita GPU y que en los nodos de login va muy lento. Separarlo evita tener una GPU reservada mientras se instalan dependencias.

# Flujo de trabajo: de tu PC a Magerit

Con las herramientas de [01-magerit.md](01-magerit.md) y [02-uv.md](02-uv.md) podemos fijar un flujo de trabajo que mantenga los proyectos ordenados y reproducibles. La idea: **se programa y se prueba en local, y en Magerit solo se ejecuta.**

Entorno de referencia:
- Ubuntu en el PC personal (WSL o una máquina virtual valen igual).
- VS Code como editor; con [Remote-SSH](til/vscode-remote-ssh.md) también puedes editar directamente en Magerit.
- [uv](02-uv.md) instalado en local y en Magerit.

## 1. (Local) Crear el proyecto

```bash
source templates/init_project.sh
init_project mi_experimento nombre.apellido@alumnos.upm.es 3.11
cd mi_experimento
uv add torch transformers
```

Se crean `pyproject.toml`, `uv.lock`, `.python-version`, `main.py`, `logs/` y los scripts `prepare_job.sh` y `execute_job.sh`. Elige la versión de Python según lo que vayas a usar: los proyectos de vLLM de este repo usan 3.11 (ver [04-vllm-on-magerit.md](04-vllm-on-magerit.md)).

## 2. (Local) Desarrollar y comprobar el código

Muchas veces no podrás ejecutar el programa entero en tu PC por falta de GPU, pero sí puedes cazar errores antes de esperar en la cola de Magerit:

- **Prueba con un caso pequeño en CPU:** un modelo diminuto, pocas filas del dataset, o un [servidor falso](../03_vllm/fake_server.py) si tu código es un cliente de vLLM.
- **Linter.** `ruff` encuentra errores de sintaxis, nombres no definidos e imports sin usar en milisegundos:
  ```bash
  uv run --with ruff ruff check .
  ```
- **Compilar a bytecode.** No necesita instalar nada y detecta los errores de sintaxis:
  ```bash
  uv run python -m py_compile main.py
  ```
- **Scripts de SLURM:** `bash -n execute_job.sh` comprueba la sintaxis de bash sin ejecutar nada.

## 3. (Local) Llevar el proyecto a Magerit

Opción recomendada: **git**. Sube el proyecto a un repositorio y haz `git clone` o `git pull` en Magerit. Así no se te olvida ningún fichero y tienes historial.

> [!IMPORTANT]
> Antes de tu primer commit en Magerit, configura tu identidad. Si no lo haces, los commits salen firmados con el usuario del clúster o con el de otra persona:
> ```bash
> git config --global user.name "Nombre Apellido"
> git config --global user.email "tu_correo@ejemplo.com"
> ```

Alternativa: `scp`. Con `-r` copia la carpeta entera:

```bash
usuario@PC:~/proyectos$ scp -r mi_experimento x123456@magerit.cesvima.upm.es:/home/x123/PROJECT/
```

> [!TIP]
> Añade un alias en `~/.ssh/config` para no escribir el usuario y el host cada vez:
> ```
> Host magerit
>     HostName magerit.cesvima.upm.es
>     User x123456
> ```
> Después: `ssh magerit`, `scp -r carpeta magerit:/home/x123/PROJECT/`.

**No se copian** la carpeta `.venv/` (se recrea en Magerit con `uv sync`), los datos (se descargan o se dejan en `PROJECT`) ni los tokens.

## 4. (Magerit) Preparar el entorno y ejecutar

```bash
ssh x123456@magerit.cesvima.upm.es
cd /home/x123/PROJECT/mi_experimento
sbatch prepare_job.sh       # 1) entorno
squeue --me                 # esperar a que termine (o mirar logs/prep-<JOBID>.log)
sbatch execute_job.sh       # 2) ejecución con GPU
tail -f logs/exec-<JOBID>.log
```

### ¿Por qué dos trabajos?
Para no malgastar recursos del clúster ni repetir trabajo:

- **`prepare_job.sh`** ejecuta `uv sync` en la partición `debug`, sin GPU. Los nodos `debug` son de corta duración y suelen tener mucha menos cola, así que los fallos de instalación aparecen pronto. Solo hay que repetirlo cuando cambian las dependencias.
- **`execute_job.sh`** ejecuta `uv run main.py` en `standard-gpu`. Como el entorno ya está listo, la GPU no se queda parada esperando a que se instalen paquetes.

> [!WARNING]
> Las rutas que aparecen en las directivas `#SBATCH` (por ejemplo `--output=logs/...`) **deben existir antes** de lanzar el trabajo. Si no, el trabajo falla sin dejar log. Si tienes el correo configurado, recibirás algo como
> `Slurm Job_id=1124194 Name=prepare_job Failed, Run time 00:00:00, FAILED, ExitCode 1`.
> Por eso los proyectos versionan `logs/.gitkeep`.

## Anexo: sin uv (venv + pip)

Si en algún momento no puedes usar uv, el equivalente clásico es:

```bash
# En local
python3.11 -m venv .venv && source .venv/bin/activate
pip install torch transformers
pip freeze > requirements.txt        # congela las versiones

# En Magerit, dentro del prepare_job.sh
module load Python/3.11.3-GCCcore-12.3.0
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# En el execute_job.sh
source .venv/bin/activate
python main.py
```

Desventajas frente a uv:
- `pip freeze` mezcla las dependencias directas con las indirectas y con las herramientas de desarrollo.
- La versión de Python no queda registrada en ningún fichero.
- Recrear el entorno es mucho más lento.

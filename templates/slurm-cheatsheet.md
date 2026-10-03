# Chuleta de comandos diarios (Magerit / SLURM)

```bash
# Conectarse
ssh x123456@magerit.cesvima.upm.es

# Encolar un trabajo (desde la carpeta del proyecto)
sbatch prepare_job.sh
sbatch execute_job.sh arg1 arg2      # los argumentos llegan al script como $1, $2...

# Ver mis trabajos y su estado (PD = en cola, R = ejecutándose)
squeue --me
squeue -j <JOBID> --start            # estimación de inicio

# Cancelar
scancel <JOBID>

# Seguir el log en directo
tail -f logs/exec-<JOBID>.log

# Historial de trabajos terminados (estado, tiempo, memoria)
sacct -j <JOBID> --format=JobID,JobName,State,Elapsed,MaxRSS

# Crear un proyecto nuevo con las plantillas
source templates/init_project.sh
init_project nombre_proyecto correo@alumnos.upm.es 3.11

# Copiar un proyecto del repositorio al directorio compartido PROJECT
cp -r nombre_proyecto "$(dirname "$HOME")/PROJECT/"
```

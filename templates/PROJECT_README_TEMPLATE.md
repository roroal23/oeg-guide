# Nombre del proyecto

> Autoría: Nombre Apellido · Estado: ✅ funciona / ⚠️ exploratorio

## Qué aprendes
Una o dos frases: qué concepto o herramienta enseña este proyecto y por qué es útil.

## Requisitos
- Python X.Y (ver `.python-version`) y [uv](../docs/02-uv.md)
- ¿CPU, Ollama en local o GPU en Magerit? ¿Qué GPU (V100 / A100)?
- Claves o cuentas necesarias (p. ej. `WANDB_API_KEY`), sin incluirlas nunca en el repo

## Cómo ejecutarlo
```bash
uv sync
uv run main.py
```
En Magerit: `sbatch prepare_job.sh` y luego `sbatch execute_job.sh`.

## Qué deberías ver
Salida esperada, ficheros que se generan o métricas que aparecen en W&B.

## Limitaciones y siguientes pasos
Lo que no funciona, lo que quedó pendiente y las ideas para continuarlo.

## Fuentes
Tutoriales, artículos o documentación en los que se basa.

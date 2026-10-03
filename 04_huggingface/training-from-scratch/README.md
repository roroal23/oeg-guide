# Entrenar un modelo de lenguaje desde cero (EsperBERTo)

> Autoría: Rodrigo Najar · Estado: ⚠️ exploratorio: el entrenamiento se completó, pero el modelo no aprendió lo suficiente

## Qué aprendes
El flujo completo para preentrenar un modelo pequeño tipo RoBERTa (84 M de parámetros) con *masked language modeling* sobre texto en esperanto:
1. Entrenar un tokenizador BPE a nivel de byte (`ByteLevelBPETokenizer`).
2. Configurar el modelo desde cero (`RobertaConfig` → `RobertaForMaskedLM`).
3. Preparar el dataset con `datasets` (sustituye al obsoleto `LineByLineTextDataset`) y `DataCollatorForLanguageModeling`.
4. Entrenar con `Trainer` y probar el resultado con `pipeline("fill-mask")`.

El notebook incluye notas propias sobre lo que hubo que cambiar respecto al tutorial original para que funcionara con versiones actuales.

## Requisitos
- GPU. En una RTX 3060, una época tardó ~1 h 15 min.
- El corpus OSCAR en esperanto (~300 MB). El propio notebook lo descarga con `wget`.

## Cómo ejecutarlo
```bash
uv run --with jupyter jupyter lab 01_how_to_train.ipynb
```

## Resultado y lecciones
El modelo no completaba bien las frases. Las causas probables están en la última celda: pocos datos (300 MB frente a ~3 GB del original) y una sola época. La pérdida reportada (41,9) es sospechosamente alta; ver la nota del notebook.

## Fuentes
Adaptado del blog de Hugging Face [*How to train a new language model from scratch*](https://huggingface.co/blog/how-to-train), de Julien Chaumond, y de su [notebook en Colab](https://colab.research.google.com/github/huggingface/blog/blob/main/notebooks/01_how_to_train.ipynb).

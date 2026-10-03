# Fine-tuning de BERT para análisis de sentimiento

> Autoría: Rodrigo Najar · Estado: ⚠️ exploratorio: el código está completo, pero el entrenamiento no llegó a terminar por falta de VRAM

## Qué aprendes
Ajustar `bert-base-uncased` para clasificar reseñas de IMDB en positivas o negativas, paso a paso:
limpieza → tokenización (`input_ids` + `attention_mask`) → `DataLoader`s → `BertForSequenceClassification` → optimizador `AdamW` + *scheduler* lineal → bucle de entrenamiento y validación en GPU.

| Fichero | Qué es |
|---|---|
| `fine_tuning_steps.ipynb` | El proceso paso a paso, con notas propias. Las salidas están limpias. |
| `fine_tuning_pipeline.py` | El mismo proceso encapsulado en una clase (`FineTuningPipeline`). |
| `sentiment_analysis.py` | Script que usa la clase. |

## Requisitos
- El dataset [*IMDB Dataset of 50K Movie Reviews*](https://www.kaggle.com/datasets/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews) (Kaggle) en `data/IMDB Dataset.csv`. La carpeta `data/` está en `.gitignore`.
- Una GPU con ~12 GB de VRAM para `max_length=512` y `batch_size=16`. En una RTX 3050 de 4 GB daba *out of memory*. Para pruebas rápidas, reduce `max_length`, `batch_size` o el número de reseñas.

## Cómo ejecutarlo
```bash
uv run --with jupyter jupyter lab fine_tuning_steps.ipynb
uv run sentiment_analysis.py
```

## Lecciones
- `tokenizer.encode_plus()` ya no existe en `transformers` 5.x: se llama directamente a `tokenizer(...)`.
- El *learning rate* importa: el valor por defecto de `AdamW` (1e-3) es demasiado alto para hacer fine-tuning de BERT. Lo habitual es entre 2e-5 y 5e-5.

## Fuentes
Adaptado de Bradney Smith, [*A Complete Guide to BERT with Code*](https://towardsdatascience.com/a-complete-guide-to-bert-with-code-9f87602e4a11/) (Towards Data Science).

# Tokenización con Hugging Face `tokenizers`

> Autoría: Rodrigo Najar · Estado: ✅ el notebook funciona (CPU)

## Qué aprendes
Las cuatro etapas de un tokenizador moderno, con ejemplos en español:
1. **Normalización:** `Lowercase`, `NFC` y `BertNormalizer` (minúsculas, quitar acentos, separar caracteres chinos).
2. **Pre-tokenización:** dividir en «palabras» con `WhitespaceSplit`, el de BERT, el de GPT-2 (`Ġ` para el espacio) y el de ALBERT/SentencePiece (`▁`).
3. **Modelo:** WordPiece de BERT; las continuaciones de palabra se marcan con `##`.
4. **Post-procesado:** añadir los tokens especiales `[CLS]` y `[SEP]` con sus ids reales del vocabulario (101 y 102).

## Cómo ejecutarlo
```bash
uv run --with jupyter jupyter lab tokenization.ipynb
```
Los tokenizadores (`bert-base-uncased`, `gpt2`, `albert-base-v1`) se descargan de Hugging Face la primera vez. No hace falta PyTorch.

## Fuentes
Basado en el artículo de Bradney Smith [*Tokenization — LLMs from scratch*](https://medium.com/@bradneysmith/tokenization-llms-from-scratch-1-cedc9f72de4e).

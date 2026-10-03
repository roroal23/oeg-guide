# Ollama básico: LLMs en tu propio PC

> Autoría: Rodrigo Najar · Estado: ✅ funciona (requiere Ollama en local)

## Qué aprendes
Primer contacto con un LLM local mediante [Ollama](https://ollama.com):
- **`llama.sh`**: envoltorio de `ollama run` que acepta la pregunta como argumento, como fichero o por tubería.
- **`translate_and_compare.py`**: traduce un texto con la API de Python de dos formas, **`generate`** (un único prompt) y **`chat`** (mensajes `system` + `user`), guarda ambas traducciones y pide al propio modelo que explique las diferencias.

## Requisitos
- [Ollama](https://ollama.com/download) instalado y en marcha (`ollama serve`).
- El modelo: `ollama pull llama3.2`.

## Cómo ejecutarlo
```bash
./llama.sh "¿Qué es una ontología?"
./llama.sh question.txt
echo "Saluda" | ./llama.sh

uv run translate_and_compare.py     # lee text-eng.txt y genera text-spa-gen.txt y text-spa-chat.txt
```

## Fuentes
`text-eng.txt` es un extracto de [*The Illustrated GPT-2*](https://jalammar.github.io/illustrated-gpt2/), de Jay Alammar.

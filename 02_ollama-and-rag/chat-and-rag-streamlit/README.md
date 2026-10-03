# Chat y RAG con Streamlit

> Autoría: Shuyi y Rodrigo Najar · Estado: ✅ funciona (requiere Ollama y una API key de Groq)

## Qué aprendes
Una app [Streamlit](https://streamlit.io) multipágina con tres ejemplos:

| Página | Qué hace | Piezas |
|---|---|---|
| **Chat Ollama** | Chat en streaming con un modelo local y un *system prompt* («explica en tres niveles») | `ollama`, `st.session_state`, `st.chat_message` |
| **RAG** | Genera un examen de 3 preguntas a partir de un PDF fijo | LangChain: `PyPDFLoader` → embeddings → Chroma → retriever → Groq |
| **RAG personalizado** | Subes tu PDF, genera un examen, respondes y el LLM te corrige | Lo mismo, más `st.file_uploader` y `st.form` |

Además, `rag_cli.py` es la versión de terminal del RAG (sin Streamlit), útil para entender la *chain* de LangChain paso a paso. Las piezas comunes están en `rag_utils.py`.

**¿Qué es RAG?** *Retrieval-Augmented Generation*: en vez de confiar en lo que el modelo «sabe», se buscan los fragmentos relevantes de tus documentos (por similitud de *embeddings*) y se le pasan como contexto en el prompt.

## Requisitos
- Ollama con `ollama pull qwen2.5:7b`, para la página de chat.
- Una API key gratuita de [Groq](https://console.groq.com): `cp .env.example .env` y pon tu clave en `.env` (está en `.gitignore`).
- Para la página **RAG**, un PDF en `resources/documento.pdf`. Nosotros usamos el discurso de ingreso de Asunción Gómez-Pérez en la Real Academia de Ingeniería («Ingeniería Ontológica»), disponible en la web de la RAI. No se incluye en el repo por derechos de autor.
- Los embeddings (`all-MiniLM-L6-v2`) se calculan en local y se descargan de Hugging Face la primera vez.

## Cómo ejecutarlo
```bash
uv run streamlit run Home.py
uv run rag_cli.py ruta/a/un.pdf
```

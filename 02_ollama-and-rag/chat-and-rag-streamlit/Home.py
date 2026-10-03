import streamlit as st

st.set_page_config(
    page_title = "Chat y RAG",
    layout = "wide",
    initial_sidebar_state = "expanded",
)

st.header("Chat y RAG con Streamlit")

st.markdown("""
Elige una página en la barra lateral:

1. **Chat Ollama**: chat en streaming contra un modelo local (`qwen2.5:7b`) con un *system prompt*.
2. **RAG**: genera un examen a partir de un PDF fijo (`resources/documento.pdf`) usando Groq.
3. **RAG personalizado**: sube tu propio PDF, genera un examen y corrige tus respuestas.
""")
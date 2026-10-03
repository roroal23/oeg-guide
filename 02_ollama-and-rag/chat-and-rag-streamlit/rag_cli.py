"""
rag_cli.py
Versión de terminal (sin Streamlit) del RAG que genera un examen a partir de un PDF.
Uso: uv run rag_cli.py [ruta_al_pdf]   (por defecto resources/documento.pdf)
"""
import sys

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq

from rag_utils import DEFAULT_PDF, LLM_MODEL, build_retriever, load_env

# Cargar API KEY de Groq (.env en la raíz del proyecto)
load_env()

pdf_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF

# 1. Cargar el PDF y procesar el texto (embeddings locales)
print("--- Analizando el PDF ---")
retriever = build_retriever(pdf_path)

# 2. Configurar el LLM (Llama 3.1 8B servido por Groq)
llm = ChatGroq(model=LLM_MODEL, temperature=0.5)

# 3. Definir el formato del examen
template = """
Actúa como un profesor riguroso. Basándote en el siguiente contexto:
{context}

Crea un examen de 3 preguntas de opción múltiple (A, B, C) sobre los puntos clave.
Al final, muestra una sección de 'Respuestas Correctas'.
"""
prompt = ChatPromptTemplate.from_template(template)

# 4. Unir las piezas (chain)
chain = (
	{"context": retriever, "question": RunnablePassthrough()}
	| prompt
	| llm
)

# 5. Ejecutar
print("--- Generando Examen ---")
result = chain.invoke("Genera un examen")
print(result.content)

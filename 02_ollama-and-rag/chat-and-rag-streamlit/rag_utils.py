"""
rag_utils.py
Piezas comunes del RAG: carga de la API key y construcción del retriever a partir de un PDF.
"""
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

PROJECT_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = PROJECT_DIR / "resources"
DEFAULT_PDF = RESOURCES_DIR / "documento.pdf"

EMBEDDINGS_MODEL = "all-MiniLM-L6-v2"  # embeddings locales (se descargan de Hugging Face)
LLM_MODEL = "llama-3.1-8b-instant"     # modelo servido por Groq


def load_env() -> None:
    """Carga GROQ_API_KEY desde el .env de la raíz del proyecto (ver .env.example)."""
    load_dotenv(PROJECT_DIR / ".env")


def build_retriever(pdf_path: str | Path):
    """Trocea el PDF, calcula los embeddings y devuelve un retriever sobre Chroma (en memoria)."""
    pages = PyPDFLoader(str(pdf_path)).load_and_split()
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
    vectorstore = Chroma.from_documents(documents=pages, embedding=embeddings)
    return vectorstore.as_retriever()

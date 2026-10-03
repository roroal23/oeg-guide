import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq

from rag_utils import DEFAULT_PDF, LLM_MODEL, build_retriever, load_env

# Cargar API KEY (fichero .env en la raíz del proyecto)
load_env()

st.set_page_config(
    page_title = "RAG",
    layout = "wide",
    initial_sidebar_state = "expanded",
)

st.header("RAG")

st.markdown(f"El modelo genera un examen a partir de un documento fijo: `{DEFAULT_PDF.relative_to(DEFAULT_PDF.parents[1])}`")


@st.cache_resource(show_spinner=False)
def get_retriever(pdf_path: str):
    # Se cachea para no recalcular los embeddings en cada clic
    return build_retriever(pdf_path)


if not DEFAULT_PDF.exists():
    st.warning(
        "No se encuentra el documento. Copia cualquier PDF en `resources/documento.pdf`. "
        "Nosotros usamos el discurso de ingreso de Asunción Gómez-Pérez en la Real Academia "
        "de Ingeniería («Ingeniería Ontológica»), disponible en la web de la RAI."
    )
    st.stop()

if st.button("Generar Examen"):
	with st.spinner("Procesando documento y generando examen..."):
		retriever = get_retriever(str(DEFAULT_PDF))

		llm = ChatGroq(model=LLM_MODEL, temperature=0.5)

		template = """
		Actúa como un profesor riguroso. Basándote en el siguiente contexto:
		{context}

		Crea un examen de 3 preguntas de opción múltiple (A, B, C) sobre los puntos clave.
		Al final, muestra una sección de 'Respuestas Correctas'.
		"""
		prompt = ChatPromptTemplate.from_template(template)

		chain = (
			{"context": retriever, "question": RunnablePassthrough()}
			| prompt
			| llm
		)

		result = chain.invoke("Genera un examen")

		st.markdown("---")
		st.markdown(result.content)

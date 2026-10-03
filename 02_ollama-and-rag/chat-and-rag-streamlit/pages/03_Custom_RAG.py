import streamlit as st
import tempfile
import os
from langchain_groq import ChatGroq

from rag_utils import LLM_MODEL, build_retriever, load_env

# 1.Configuracion
st.set_page_config(page_title="Tutor RAG", layout="wide")
st.header("Tutor Inteligente: Sube tu PDF")
load_env()  # GROQ_API_KEY desde el .env de la raíz del proyecto

# Inicializar sesion
if "messages" not in st.session_state:
	st.session_state["messages"] = []
	st.session_state["generated_exam"] = None

# 2.Sidebar para subir el archivo
with st.sidebar:
	st.subheader("Documentacion")
	uploaded_file = st.file_uploader("Sube un archivo PDF", type="pdf")

# 3. Logica de procesamiento al subir un archivo
if uploaded_file and "retriever" not in st.session_state:
		# Guardar en archivo temporal
		with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
			tmp.write(uploaded_file.getvalue())
			tmp_path = tmp.name

		# Procesar PDF
		with st.spinner("Analizando documento..."):
			st.session_state["retriever"] = build_retriever(tmp_path)
			os.remove(tmp_path) # limpiar el archivo temporal
		st.success("Documento procesado correctamente.")

# 4.Generacion del examen
if "retriever" in  st.session_state and st.session_state["generated_exam"] is None:
	if st.button("Generar Examen"):
		with st.spinner("Creando examen..."):
			llm = ChatGroq(model=LLM_MODEL, temperature=0)

			context = st.session_state["retriever"].invoke("puntos clave del documento")
		prompt = f"""
			Basado en este contexto: {context}, genera 3 preguntas de opcion multiple (A, B, C).
			Devuelve el resultado exactamente en este formato:

			### PREGUNTAS
			1. [Pregunta] A) B) C)
			2. [Pregunta] A) B) C)
			3. [Pregunta] A) B) C)

			### OPCION_CORRECTA
			1. [Letra]
			2. [Letra]
			3. [Letra]
			"""
		response = llm.invoke(prompt)

		st.session_state["generated_exam"] = response.content
		st.rerun()

# 5.Mostrar el examen y chat
if st.session_state["generated_exam"]:
	content = st.session_state["generated_exam"]

	if "OPCION_CORRECTA" in content:
		parts = content.split("### OPCION_CORRECTA")
		questions_only = parts[0]
		answer_key = parts[1]
	else:
		# Si falla ocultar la solución, dejamos que muestre todo.
		questions_only = content
		answer_key = "No se encontró clave"
		st.warning("El modelo no generó el formato correctamente")

	st.markdown(questions_only)

	with st.form("exam_form"):
		user_answers = st.text_area("Escribe tus respuestas (Ej: 1:A, 2:B, 3:C)")
		submit = st.form_submit_button("Enviar")

	if submit:
		st.write("### Evaluando...")

		eval_prompt = f"""
		La clave de respuestas es: {answer_key}
		El usuario ha respondido: {user_answers}
		Compara las respuestas del usuario con la clave de respuestas y dime si acertó cada una.
		"""

		llm = ChatGroq(model=LLM_MODEL, temperature=0)

		response = llm.invoke(eval_prompt)

		st.success("Resultados:")
		st.write(response.content)


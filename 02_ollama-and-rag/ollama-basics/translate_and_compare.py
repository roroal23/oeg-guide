import ollama

# --- CONFIGURACIÓN ---
MODEL = 'llama3.2'
SOURCE_LANGUAGE = 'inglés'
SOURCE_CODE = 'eng'
TARGET_LANGUAGE = 'español'
TARGET_CODE = 'spa'
FILE_PREFIX = 'text'
TRANSLATE_INSTRUCTION = f"""Eres un traductor profesional. Traduce el siguiente texto del {SOURCE_LANGUAGE} al {TARGET_LANGUAGE}. Mantén el formato
                    original y responde únicamente con la traducción."""

COMPARE_INSTRUCTION = f"""A continuación te daré 2 textos: ambos fueron generados por {MODEL}. La principal diferencia es que 
                    el primero fue generado con la herramienta 'generate' y el segundo con la herramienta 'chat' (la orden 
                    descompuesta en un mensaje 'system' y uno 'user'). Menciona y explica el porque de las diferencias entre
                    ambos textos."""

# --- FUNCIONES ---
def read_file(filename: str) -> str:
    content = ''
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def write_file(filename: str, content: str):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)


def translate_by_generate(text: str) -> str:
    response = ollama.generate(model = MODEL, prompt = f"{TRANSLATE_INSTRUCTION}\n{text}")
    return response['response']

def translate_by_chat(text: str) -> str:
    response = ollama.chat(model = MODEL, messages = [
        {'role': 'system', 'content': TRANSLATE_INSTRUCTION},
        {'role': 'user', 'content': text}
    ])
    return response['message']['content']

def explain_diff(text1: str, text2: str) -> str:
    response = ollama.chat(model = MODEL, messages = [
        {'role': 'system', 'content': COMPARE_INSTRUCTION},
        {'role': 'user', 'content': text1},
        {'role': 'user', 'content': text2}
    ])
    return response['message']['content']

if __name__ == "__main__":
    SOURCE_FILE = f'{FILE_PREFIX}-{SOURCE_CODE}.txt'
    TARGET_FILE_GEN = f'{FILE_PREFIX}-{TARGET_CODE}-gen.txt'
    TARGET_FILE_CHAT = f'{FILE_PREFIX}-{TARGET_CODE}-chat.txt'

    print("---> Leyendo fichero...")
    raw_text = read_file(SOURCE_FILE)
    print("---> Iniciando traducciones...")

    translation_gen = translate_by_generate(raw_text)
    print("--> Traduccion usando generate:")
    print(translation_gen)

    translation_chat = translate_by_chat(raw_text)
    print("---> Traduccion usando chat:")
    print(translation_chat)

    print("---> Guardando en ficheros...")
    write_file(TARGET_FILE_GEN, translation_gen)
    write_file(TARGET_FILE_CHAT, translation_chat)

    print("---> Revisando diferencias en ficheros...")
    explanation = explain_diff(translation_gen, translation_chat)
    print(explanation)
# pylint: disable=missing-function-docstring

""" 
mock.py
Prueba de una respuesta "mock" de LiteLLM con y sin stream.
Nos permite conocer la estructura de una respuesta sin usar ninguna llamada a la API.
"""
from litellm import completion, ModelResponse, CustomStreamWrapper

def print_response(response: ModelResponse):
    """
        Llamar completion sin stream devuelve un objeto ModelResponse, que contiene la
        respuesta del LLM, el modelo usado, asi como detalles sobre el uso de tokens.
        Este objeto puede transformarse de forma natural a formato JSON
    """
    json_string = response.model_dump_json(indent = 4)
    print(json_string)
    response_str = response["choices"][0]["message"]["content"]
    print(f"Respuesta:\n{response_str}")

def print_stream(response : CustomStreamWrapper):
    """
        Llamar a completion con stream nos permite obtener la respuesta a medida que se 
        construye: Devuelve pequeños 'chunks' con parte de la respuesta, de modo que, 
        nosotros debemos reconstruir el mensaje si queremos usarlo luego
        Al acabar devuelve un chunk sin contenido ("content" = None)
    """
    response_str = "" #Debemos reconstruir la respuesta a medida de que llega
    for chunk in response:
        print(chunk)
        if chunk_str := chunk["choices"][0]["delta"]["content"]:
            response_str += chunk_str
    print(f"Respuesta:\n{response_str}")

def main():
    model = "gpt-3.5-turbo"
    messages = [{
        "role":"user",
        "content":"Prueba de peticion"
        }]

    print("=== SIN STREAM ===\n")
    response = completion(model = model, messages = messages,
                            mock_response = "Mensaje de prueba")
    if isinstance(response, ModelResponse):
        print_response(response)
    print("=== CON STREAM ===\n")
    response_stream = completion(model = model, messages = messages, stream = True,
                                mock_response = "Mensaje de prueba")
    if isinstance(response_stream, CustomStreamWrapper):
        print_stream(response_stream)

if __name__ == '__main__':
    main()

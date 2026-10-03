# LiteLLM: anatomía de una respuesta (sin API key)

> Autoría: Rodrigo Najar · Estado: ✅ funciona (CPU, sin red)

## Qué aprendes
[LiteLLM](https://docs.litellm.ai/) da una interfaz única (`completion()`) para hablar con muchos proveedores: OpenAI, Groq, un servidor vLLM local... Con `mock_response` devuelve una respuesta simulada sin llamar a ninguna API, lo que permite ver la estructura de los objetos:

- **Sin streaming:** un `ModelResponse` con `choices[0].message.content` y el uso de tokens (`usage`).
- **Con streaming:** un iterador de *chunks* (`choices[0].delta.content`) con los que hay que reconstruir el mensaje. El último llega con `content=None` y `finish_reason='stop'`.

Es la misma librería que usan los clientes de [`03_vllm`](../../03_vllm) para hablar con vLLM.

## Cómo ejecutarlo
```bash
uv run mock.py
```

## Qué deberías ver
El JSON completo del `ModelResponse`, seguido de los chunks del stream (`'Men'`, `'saj'`, `'e d'`...) y del mensaje reconstruido: `Mensaje de prueba`.

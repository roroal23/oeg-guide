"""
fake_server.py
Servidor HTTP mínimo que imita los endpoints de `vllm serve` que usan los clientes de esta
carpeta (/health, /v1/models y /v1/chat/completions). Sirve para probar la lógica de los
clientes en local, sin GPU ni modelo: siempre responde con el mismo texto.

Solo usa la librería estándar:
    python3 fake_server.py [puerto]        # por defecto 8000
"""
import json
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ANSWER = "Correcta. (Respuesta fija del servidor falso)"


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send_json({})
        elif self.path == "/v1/models":
            self._send_json({"object": "list", "data": [{"id": "modelo-falso", "object": "model"}]})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self._send_json({"error": "not found"}, 404)
            return
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        prompt_tokens = sum(len(m["content"].split()) for m in request["messages"])
        completion_tokens = len(ANSWER.split())
        time.sleep(0.05)  # simula algo de latencia
        self._send_json({
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request["model"],
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": ANSWER},
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        })

    def log_message(self, *args):  # silencia el log por petición
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"Servidor falso escuchando en http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()

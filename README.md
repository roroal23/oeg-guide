# LLMs en Magerit: apuntes y proyectos del OEG

Apuntes y proyectos de nuestros primeros meses en el [Ontology Engineering Group](https://oeg.fi.upm.es) (UPM): cómo trabajar en el superordenador **Magerit**, cómo gestionar proyectos de Python con **uv**, y una serie de proyectos pequeños sobre **LLMs**, desde ejecutarlos en tu PC con Ollama hasta hacer *benchmarks* asíncronos con vLLM en GPU.

No es un curso cerrado, sino exploraciones reales, limpias y documentadas. Cada proyecto indica si funciona, si es exploratorio y de qué tutorial parte.

## Por dónde empezar

1. **Infraestructura.** Lee [`docs/`](docs/) en orden:
   1. [Magerit](docs/01-magerit.md): acceso, módulos, SLURM.
   2. [uv](docs/02-uv.md): entornos y dependencias.
   3. [Flujo de trabajo PC → Magerit](docs/03-local-to-magerit-workflow.md).
   4. [vLLM en Magerit](docs/04-vllm-on-magerit.md).
2. **Plantillas.** [`templates/`](templates/) tiene los scripts de SLURM y `init_project.sh` para crear tus propios proyectos.
3. **Proyectos**, en este orden. Las ramas HF y Evaluación son independientes:

| Tema | Proyecto | Qué aprendes | Requisitos | Autoría |
|---|---|---|---|---|
| **01 Fundamentos** | [concurrency-and-parallelism](01_fundamentals/concurrency-and-parallelism) | Hilos, procesos, asyncio y el GIL | CPU | Rodrigo |
| | [litellm-mock](01_fundamentals/litellm-mock) | Estructura de las respuestas de un LLM (con y sin *streaming*) | CPU | Rodrigo |
| **02 Ollama y RAG** | [ollama-basics](02_ollama-and-rag/ollama-basics) | LLMs locales; `generate` vs `chat` | Ollama | Rodrigo |
| | [chat-and-rag-streamlit](02_ollama-and-rag/chat-and-rag-streamlit) | App de chat y RAG sobre PDFs (LangChain, Chroma, Groq) | Ollama + clave de Groq | Shuyi, Rodrigo |
| **03 vLLM** | [01-offline](03_vllm/01-offline) | `LLM.generate` y parámetros de muestreo | GPU (Magerit) | Rodrigo |
| | [02-benchmark-wandb](03_vllm/02-benchmark-wandb) | Benchmark de varios modelos con Weights & Biases | GPU (Magerit) | Shuyi |
| | [03-openai-server](03_vllm/03-openai-server) | `vllm serve` y clientes compatibles con OpenAI | GPU (Magerit) | Rodrigo |
| | [04-scaling-async](03_vllm/04-scaling-async) | Miles de peticiones concurrentes con asyncio | GPU (Magerit) | Rodrigo, Shuyi |
| | [05-structured-scaling](03_vllm/05-structured-scaling) | El mismo benchmark con config YAML, Pydantic y productor-consumidor | GPU (Magerit) | Rodrigo, Shuyi |
| **04 Hugging Face** | [tokenization](04_huggingface/tokenization) | Las etapas de un tokenizador | CPU | Rodrigo |
| | [fine-tuning](04_huggingface/fine-tuning) | Fine-tuning de BERT para sentimiento | GPU ~12 GB | Rodrigo |
| | [training-from-scratch](04_huggingface/training-from-scratch) | Preentrenar un RoBERTa pequeño | GPU | Rodrigo |
| **05 Evaluación** | [metrics](05_evaluation/metrics) | BLEU y ROUGE en la práctica + teoría de evaluación | CPU | Rodrigo |

Además, [docs/05-evaluation-datasets.md](docs/05-evaluation-datasets.md) reúne datasets y métricas para evaluar LLMs en español (Shuyi).

## Primeros pasos con uv

Cada carpeta de proyecto es un proyecto [uv](docs/02-uv.md) independiente, con su `pyproject.toml`, su `uv.lock` y su `.python-version`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh     # instalar uv (una vez)
git clone <este-repo> && cd <este-repo>
cd 01_fundamentals/concurrency-and-parallelism
uv run sequential.py                                # uv crea el entorno y ejecuta
bash compare.sh
```

En Magerit, desde la carpeta de un proyecto de [`03_vllm`](03_vllm): `sbatch prepare_job.sh` y luego `sbatch execute_job.sh`.

## Estructura

```
docs/            Apuntes: Magerit, uv, flujo de trabajo, vLLM, datasets; til/ para trucos cortos
templates/      Scripts de SLURM, init_project.sh y una plantilla de README
01_fundamentals/  02_ollama-and-rag/  03_vllm/  04_huggingface/  05_evaluation/
```

## Contribuir
Para añadir un proyecto o un truco, consulta [CONTRIBUTING.md](CONTRIBUTING.md).

## Autores
- **Rodrigo Najar**
- **Shuyi**

## Licencia
- Código: [MIT](LICENSE).
- Apuntes de [`docs/`](docs/) y los README: [CC BY 4.0](docs/LICENSE).

Los proyectos adaptados de tutoriales indican su fuente en su README.

# Cómo contribuir

Pautas para añadir proyectos y apuntes manteniendo el repositorio coherente.

## Añadir un proyecto
1. Elige la carpeta de tema (`01_fundamentals`, `02_ollama-and-rag`, `03_vllm`...) o crea una nueva con el siguiente número.
2. Crea el proyecto con las plantillas:
   ```bash
   cd 03_vllm
   source ../templates/init_project.sh
   init_project 06-mi-experimento tu.correo@alumnos.upm.es 3.11
   ```
3. Declara **todas** las dependencias que importas con `uv add` (nada de `pip install` suelto) y versiona `pyproject.toml`, `uv.lock` y `.python-version`.
4. Escribe el README a partir de [`templates/PROJECT_README_TEMPLATE.md`](templates/PROJECT_README_TEMPLATE.md): qué aprendes, requisitos, cómo ejecutarlo, qué deberías ver, limitaciones y fuentes. Indica el estado con sinceridad: un experimento fallido bien explicado también enseña.
5. Añade una fila a la tabla del [README](README.md) principal.

## Añadir un TIL (*Today I Learned*)
Un truco corto que no merece un proyecto: un fichero en [`docs/til/`](docs/til/) con contexto, solución y avisos. Ejemplo: [vscode-remote-ssh.md](docs/til/vscode-remote-ssh.md).

## Antes de hacer commit
- [ ] **Nada de secretos.** Ni tokens de Hugging Face, ni claves de API, ni `.env` (usa un `.env.example`). Para W&B, `wandb login` guarda la clave en `~/.netrc`, fuera del repo.
- [ ] **Nada de datos personales.** Ni tu usuario del clúster (usa `x123456` en los ejemplos), ni correos, ni rutas como `/home/tu_usuario`.
- [ ] **Nada de ficheros generados ni pesados.** Logs de SLURM, `outputs/`, `wandb/`, datasets, PDFs, pesos de modelos. El `.gitignore` cubre la mayoría; revisa `git status` de todas formas.
- [ ] **Notebooks sin errores ni rutas locales en las salidas.** Si no se pudo ejecutar entero, limpia las salidas (*Clear All Outputs*).
- [ ] `uv run --with ruff ruff check .` sin errores, y `bash -n` sobre los scripts `.sh`.
- [ ] **Configura git en Magerit** antes de tu primer commit allí (`git config --global user.name/user.email`). Si no, el commit sale a nombre del usuario del clúster.

## Estilo
- Documentación en español. El código puede tener nombres en inglés, pero mejor comentado en español.
- Los scripts de SLURM siguen las [convenciones de las plantillas](templates/README.md): sin `--chdir`, logs en `logs/` y cachés en `PROJECT`.

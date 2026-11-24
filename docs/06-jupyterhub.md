# JupyterHub del AIInnovation: lo que aprendimos

El JupyterHub del AIInnovation ofrece un JupyterLab en el navegador: se entra con usuario y contraseña desde la web, sin `ssh`. Al levantar el entorno se eligen dos cosas:

- **Una imagen prefabricada:** Python 3.11, Python 3.10 o herramientas de R.
- **El hardware:** una A100, una H100 o sin gráfica.

Para trabajar en la terminal, abre el *Launcher* y elige **Other → Terminal**. La terminal se abre directamente como **root**.

Estos apuntes cuentan qué nos pasó al ejecutar allí un proyecto pensado para la terminal de un PC (con git y [uv](02-uv.md)), por qué pasa y cómo trabajar sin pelearse con los permisos.

> [!NOTE]
> Esta es la situación en noviembre de 2026. Si cambia la configuración del hub, repite el [diagnóstico](#diagnóstico-por-qué-pasa) antes de aplicar nada de esto.

## El síntoma

El código del proyecto se ejecutaba sin problemas, pero cualquier comando de git fallaba:

```
fatal: detected dubious ownership in repository at '/home/jovyan/mi-proyecto'
```

El `.git` estaba ahí: git lo encontraba, pero se negaba a usarlo.

## Diagnóstico: por qué pasa

```bash
id                                    # quién eres: uid=0(root)
ls -ldn ~ ~/mi-proyecto ~/mi-proyecto/.git
# drwxr-xr-x ... 65534 65534 ... /home/jovyan
# drwxr-xr-x ... 65534 65534 ... /home/jovyan/mi-proyecto
# drwxr-xr-x ... 65534 65534 ... /home/jovyan/mi-proyecto/.git
```

`ls -n` muestra el uid y el gid en número en vez de con nombre. Lo que vimos:

- El uid/gid `65534` es `nobody`.
- El home (`/home/jovyan`) está en un volumen de red (NFS) con **`root_squash`**: el servidor NFS trata a root como `nobody`, así que todo lo que root escribe ahí queda en disco a nombre de `nobody`.
- No es solo el repo: **todo el home es de `nobody`**, con permisos `755` (solo el dueño puede escribir).

| Usuario | Cómo lo ve el disco | ¿Puede escribir en `~`? |
|---|---|---|
| `root` (uid 0) | como `nobody` (65534), el dueño | **Sí** |
| `jovyan` (uid 1000) | como 1000, que no es el dueño | **No** (solo lectura) |

Consecuencias:

- **Como root se puede trabajar:** escribe como `nobody`, que es el dueño de todo.
- **Git falla como root** porque compara tu uid (0) con el del dueño del repo (65534) y no sabe que en disco son el mismo. Desde la versión 2.35.2, git se niega a trabajar en repositorios de otro usuario (protección frente a la CVE-2022-24765).
- **`chown` no funciona**, ni siquiera como root: root actúa como `nobody` y no puede cambiar dueños.
- **Como `jovyan` no se puede ni clonar:** `fatal: could not create work tree dir 'mi-proyecto': Permission denied`.
- **Root y jovyan comparten el home.** El `HOME` de root es `/home/jovyan`, así que `~/.local/bin`, `~/.gitconfig`, las cachés, etc. son las mismas para los dos.

## Qué NO hacer

> [!WARNING]
> - **No trabajes como `jovyan`.** No tiene permisos de escritura en el home.
> - **No uses `chmod 777` ni `chmod -R` para que jovyan pueda escribir.** Acabarás con ficheros de jovyan que root no puede tocar y ficheros de `nobody` que jovyan no puede tocar.
> - **No uses `safe.directory '*'`.** Desactiva la comprobación para todos los repositorios; añade solo la ruta del tuyo.
> - **No borres el repo con `rm -rf` para clonarlo de nuevo sin hacer antes una copia.** Perderías todo lo que no está versionado: bases de datos locales (p. ej. `mlflow.db`), resultados, datos, `.env`…

## Solución: root y `safe.directory` solo para tu repo

Trabaja **siempre como root** (la terminal ya se abre así) y añade una excepción de git **solo** para tu repositorio.

### Instalar uv

El instalador de [02-uv.md](02-uv.md) (`curl ... | sh`) **no funciona en el hub**. Lo que sí funciona es instalarlo con `pip`:

```bash
pip install uv                          # una vez
export PATH="$HOME/.local/bin:$PATH"    # en cada sesión de terminal
```

> [!IMPORTANT]
> El `export PATH` no se guarda: repítelo cada vez que abras una terminal. Si no, verás `uv: command not found`.

Por lo demás, uv funciona igual que en tu PC (`uv sync`, `uv run`, `uv add`…): consulta [02-uv.md](02-uv.md).

### Tu versión de Python, no la de la imagen

Las imágenes del hub fijan la versión de Python (3.11 o 3.10). Con uv, eso deja de ser una restricción: manda el fichero `.python-version` del proyecto. Si la imagen no trae esa versión, `uv sync` la descarga y la guarda en `~/.local/share/uv/python`. Como está dentro del home, se conserva entre sesiones.

```bash
cat .python-version          # p. ej. 3.12
uv sync                      # si la imagen no trae esa versión, uv la descarga
uv run python --version      # la del proyecto, no la de la imagen
```

Así, al levantar el entorno, la elección que de verdad importa es el hardware: elige la GPU que necesites (A100, H100 o ninguna), cualquier imagen de Python, y deja que uv se encargue de la versión.

### Clonar el repositorio (una vez)

```bash
cd ~
git clone https://github.com/<org>/<repo>.git
cd <repo>
git config --global --add safe.directory "$PWD"   # equivale a /home/jovyan/<repo>
git status                                        # ya no debe dar error
uv sync
```

`safe.directory` necesita la ruta absoluta del repositorio. Si lo ejecutas desde dentro del repo, `"$PWD"` la pone por ti. Se guarda en `~/.gitconfig`, así que basta con hacerlo una vez por repositorio.

> [!IMPORTANT]
> Antes de tu primer commit en el hub, configura tu identidad. Si no, git no sabe quién eres y los commits pueden salir a nombre de `root`:
> ```bash
> git config --global user.name "Nombre Apellido"
> git config --global user.email "tu_correo@ejemplo.com"
> ```

> [!NOTE]
> El arreglo de verdad (que el home sea del uid 1000 y se pueda trabajar como jovyan) no está en nuestra mano. Depende de quien administre el JupyterHub, que tendría que cambiar la configuración del volumen (el export NFS, `fsGroup` o un *init container* que haga `chown`) o la del *spawner*.

## Pasar carpetas grandes del PC al hub

Para subir una carpeta con muchos ficheros (resultados de experimentos, datos…), empaquétala en un solo fichero, súbelo con la interfaz de JupyterLab y descomprímelo en la terminal. En los ejemplos, `<carpeta>` es el nombre de la carpeta que quieres subir.

### En el PC

```bash
cd <directorio>                                           # el que contiene <carpeta>
tar -czf <carpeta>.tar.gz <carpeta>/
sha256sum <carpeta>.tar.gz > <carpeta>.tar.gz.sha256      # hash para verificar en el hub
ls -lh <carpeta>.tar.gz
```

Si el `.tar.gz` es muy grande (cientos de MB o más), trocéalo. Así, si el proxy corta la conexión, solo repites el trozo que falló y no toda la subida:

```bash
split -b 300M <carpeta>.tar.gz <carpeta>.tar.gz.part-
```

### Subida

En el explorador de ficheros de JupyterLab (panel izquierdo), entra en la carpeta de destino y arrastra el `.tar.gz` (o los trozos) junto con el `.sha256`. Espera a que termine la barra de progreso.

### En la terminal del hub

```bash
cd <destino>
cat <carpeta>.tar.gz.part-* > <carpeta>.tar.gz      # solo si lo troceaste
sha256sum -c <carpeta>.tar.gz.sha256                # debe terminar en OK
tar --no-same-owner -xzf <carpeta>.tar.gz
```

Verifica y limpia:

```bash
tar -tzf <carpeta>.tar.gz | wc -l      # entradas en el tar
find <carpeta> | wc -l                 # entradas en disco (deben coincidir)
rm -f <carpeta>.tar.gz <carpeta>.tar.gz.sha256 <carpeta>.tar.gz.part-*
```

### Por qué `--no-same-owner`

Si eres root, `tar` intenta que los ficheros vuelvan a ser de su dueño original (el uid 1000 de tu PC), y aquí no puede:

```
Cannot change ownership to uid 1000, gid 1000: Operation not permitted
```

Es inofensivo, porque los ficheros se extraen bien y quedan como `nobody`, que es lo correcto aquí. Pero `tar` termina con código de error, y `--no-same-owner` evita tanto el mensaje como el error.

### Experimentos registrados en una base de datos

Si tu proyecto registra los experimentos en una base de datos local (por ejemplo, MLflow con SQLite), copiar la carpeta de resultados trae los ficheros, pero **no registra** la ejecución en la base de datos del hub. Para verla en la interfaz de esa herramienta, sube también la base de datos (y el almacén de artefactos, si lo usas) o vuelve a registrar la ejecución en el hub. Subir la base de datos sustituye a la que ya hay en el hub, así que haz una copia antes.

## Chuleta

```bash
# Diagnóstico (65534 = nobody)
id && ls -ldn ~ <ruta>

# En cada sesión de terminal
export PATH="$HOME/.local/bin:$PATH"

# Una vez
pip install uv
cd ~ && git clone https://github.com/<org>/<repo>.git && cd <repo>
git config --global --add safe.directory "$PWD"
git config --global user.name "Nombre Apellido"
git config --global user.email "tu_correo@ejemplo.com"
uv sync

# PC → hub
tar -czf <carpeta>.tar.gz <carpeta>/ && sha256sum <carpeta>.tar.gz > <carpeta>.tar.gz.sha256    # PC
sha256sum -c <carpeta>.tar.gz.sha256 && tar --no-same-owner -xzf <carpeta>.tar.gz && rm <carpeta>.tar.gz*   # hub
```

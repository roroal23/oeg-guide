# TIL: editar en Magerit con VS Code Remote-SSH

## Contexto
Necesitaba editar código directamente en Magerit sin usar `vim`.

## Qué es
**Remote-SSH** es una extensión de VS Code que abre una sesión remota completa por SSH. La interfaz corre en tu PC, pero todo lo demás (ficheros, terminal, extensiones de Python) corre en Magerit.

## Configuración
1. Instala la extensión **Remote-SSH** en VS Code.
2. (Opcional, recomendado) Añade un alias en `~/.ssh/config`:
   ```
   Host magerit
       HostName magerit.cesvima.upm.es
       User x123456
   ```
3. En la barra lateral, abre *Remote Explorer* y pulsa **New Remote** (o `F1` → *Remote-SSH: Connect to Host...*).
4. Escribe `magerit` (el alias) o `ssh x123456@magerit.cesvima.upm.es`.
5. Elige *Connect* (o *Connect in New Window*) e introduce tu contraseña.
6. *File → Open Folder* → `/home/x123/PROJECT/mi_proyecto`.

## A tener en cuenta
- VS Code instala su servidor en `~/.vscode-server` (en tu `$HOME`), que ocupa varios cientos de MB de tu cuota.
- La sesión corre en un **nodo de login**: sirve para editar y lanzar `sbatch`, no para ejecutar cosas pesadas. Eso va siempre en un trabajo de SLURM.

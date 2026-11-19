# 04 · Databricks CLI y entorno local

La **CLI** (línea de comandos) te permite manejar Databricks desde la terminal: subir archivos al
volumen, lanzar jobs y desplegar el proyecto. El **entorno virtual** tiene las librerías de Python
para trabajar localmente.

## A. Entorno virtual de Python (ya creado en este repo)

El proyecto usa [uv](https://docs.astral.sh/uv/) y Python 3.12. Desde la carpeta del proyecto:

```bash
uv sync                 # crea/actualiza .venv con las dependencias de pyproject.toml
source .venv/bin/activate
uv run pytest           # debe decir "3 passed"
```

En VS Code: `Cmd+Shift+P` → *Python: Select Interpreter* → elige `.venv`.

## B. Instalar la CLI de Databricks

```bash
brew tap databricks/tap
brew trust databricks/tap   # Homebrew reciente pide confiar explícitamente en taps de terceros
brew install databricks
databricks --version    # debe mostrar v0.2xx o superior
```

## C. Autenticarte con tu workspace

```bash
databricks auth login --host https://dbc-xxxxxxxx-xxxx.cloud.databricks.com
```

- Usa la URL que guardaste en el paso 01.
- Te pedirá un nombre de perfil: escribe `DEFAULT` (Enter).
- Se abre el navegador para que inicies sesión (OAuth). Al volver a la terminal queda guardado en
  `~/.databrickscfg` (fuera del repo; nunca lo subas a GitHub).

Prueba:

```bash
databricks current-user me      # muestra tu usuario
databricks catalogs list        # lista catálogos (verás 'workspace', 'system', 'samples'...)
```

## D. Completar el bundle

[databricks.yml](../databricks.yml) no lleva la URL del workspace (el repo es público): usa el
perfil `DEFAULT` que acabas de crear. Compruébalo con:

```bash
databricks bundle validate
```

Si dice `Validation OK!`, todo quedó conectado. (El bundle se usará en la etapa 2 para desplegar el
job y los tableros desde código.)

## ✅ Checkpoint
`databricks current-user me` devuelve tu usuario y `uv run pytest` pasa.

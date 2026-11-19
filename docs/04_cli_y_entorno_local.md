# 04 · Entorno local (opcional)

En este proyecto **todo lo de Databricks se hace desde la interfaz web**: crear objetos, subir
archivos, crear jobs y tableros. Así se aprende qué hace cada pieza.

El entorno local solo sirve para editar código en VS Code y correr las pruebas antes de hacer
`git push`. Después, en Databricks, haces **Pull** en el Git folder (paso 03).

## Entorno virtual de Python (ya creado en este repo)

El proyecto usa [uv](https://docs.astral.sh/uv/) y Python 3.12. Desde la carpeta del proyecto:

```bash
uv sync                 # crea/actualiza .venv con las dependencias de pyproject.toml
uv run pytest           # corre las pruebas
```

En VS Code: `Cmd+Shift+P` → *Python: Select Interpreter* → elige `.venv`.

## Flujo de trabajo

1. Editas en VS Code → `uv run pytest` → `git commit` → `git push`.
2. En Databricks: **Workspace** → `ipc-databricks` → botón de la rama (`main`) → **Pull**.
3. Corres el notebook en Databricks.

> Más adelante, si quieres automatizar despliegues, existe la *Databricks CLI* y los *Asset
> Bundles* ([databricks.yml](../databricks.yml)). Son opcionales y no se usan en esta guía.

## ✅ Checkpoint
`uv run pytest` pasa en tu computador.

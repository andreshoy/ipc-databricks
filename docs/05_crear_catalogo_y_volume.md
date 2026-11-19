# 05 · Crear el catálogo, los esquemas y el volumen

Vas a correr tu primer notebook: [notebooks/00_setup_catalogo.py](../notebooks/00_setup_catalogo.py).

## Pasos

1. En Databricks: **Workspace** → `ipc-databricks` → `notebooks` → abre **00_setup_catalogo**.
2. Arriba a la derecha, en el selector de cómputo, verifica que diga **Serverless** (conéctalo si
   aparece *Connect*).
3. Clic en **Run all**. La primera ejecución tarda unos segundos mientras arranca el cómputo.
4. Al final verás una tabla con `bronze`, `silver`, `gold` (y `default`, `information_schema`).

### Si falla con un error de permisos al crear el catálogo
En la parte superior del notebook hay un campo (widget) **Catálogo**. Cámbialo a `workspace`, corre
de nuevo, y avísame para cambiar el valor por defecto en [src/ipc/config.py](../src/ipc/config.py).

## Verificar en la interfaz

1. Menú **Catalog** → busca `ipc`.
2. Despliega `bronze` → **Volumes** → `raw`. Dentro verás las carpetas `historico` y `mensual`.

## ✅ Checkpoint
Existe el volumen `ipc.bronze.raw` con las carpetas `historico/` y `mensual/`.

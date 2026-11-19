# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Verificar los archivos del volumen
# MAGIC
# MAGIC Revisa todo lo que subiste a `/Volumes/ipc/bronze/raw/`:
# MAGIC
# MAGIC 1. **Inventario**: qué hay en cada carpeta (`historico`, `mensual`, `referencia`).
# MAGIC 2. **Resumen por archivo**: si está completo o truncado, qué meses trae, cuántos niveles de
# MAGIC    ingreso y geografías, y si el total nacional cuadra con el anexo oficial del DANE.
# MAGIC 3. **Cobertura**: meses con datos por año, para comprobar que no haya huecos.
# MAGIC
# MAGIC Dale **Run all** y mándame un pantallazo de las tres tablas.

# COMMAND ----------

# MAGIC %pip install openpyxl --quiet

# COMMAND ----------

import os
import sys

# El código del proyecto (carpeta src/ del repo) se importa desde el Git folder
sys.path.insert(0, os.path.abspath("../src"))

from ipc import verificacion

dbutils.widgets.text("catalogo", "ipc", "Catálogo")
base = f"/Volumes/{dbutils.widgets.get('catalogo')}/bronze/raw"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Inventario

# COMMAND ----------

import pandas as pd

inventario = pd.DataFrame(
    [
        {"carpeta": c, "archivo": f, "MB": round(os.path.getsize(f"{base}/{c}/{f}") / 1e6, 2)}
        for c in sorted(os.listdir(base))
        if os.path.isdir(f"{base}/{c}")
        for f in sorted(os.listdir(f"{base}/{c}"))
    ]
)
display(inventario.groupby("carpeta").size().rename("archivos").reset_index())
display(inventario)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Resumen por archivo
# MAGIC Esperado: todos `✅ completo`, `solo_numero_indice = true` y `dif_max_vs_anexo = 0`.

# COMMAND ----------

resumen = verificacion.verificar_carpetas(base)
display(resumen)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Cobertura (meses con datos por año)
# MAGIC Esperado: 12 en cada año desde 2019 (y los meses publicados del año actual) para los 5
# MAGIC niveles de ingreso, y 24 geografías por año en la última fila.

# COMMAND ----------

display(verificacion.cobertura(base).reset_index())

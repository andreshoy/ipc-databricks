# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Explorar un archivo exportado
# MAGIC
# MAGIC Lee **un** archivo del volumen con el lector del proyecto (`src/ipc/lector.py`) y muestra su
# MAGIC estructura. Para revisar todos los archivos usa el notebook **02_verificar_volumen**.
# MAGIC
# MAGIC Widgets: `carpeta` (historico / mensual) y `archivo` (vacío = el primero de la carpeta).

# COMMAND ----------

# MAGIC %pip install openpyxl --quiet

# COMMAND ----------

import os
import sys

sys.path.insert(0, os.path.abspath("../src"))  # código del proyecto en el Git folder

from ipc.lector import leer_exportacion

dbutils.widgets.text("catalogo", "ipc", "Catálogo")
dbutils.widgets.text("carpeta", "mensual", "Subcarpeta del volumen")
dbutils.widgets.text("archivo", "", "Archivo (vacío = el primero)")

ruta = f"/Volumes/{dbutils.widgets.get('catalogo')}/bronze/raw/{dbutils.widgets.get('carpeta')}"
archivos = sorted(f for f in os.listdir(ruta) if f.lower().endswith(".xlsx"))
print("Archivos en la carpeta:", archivos)
assert archivos, f"No hay archivos .xlsx en {ruta}. Súbelos primero (docs/06)."

archivo = dbutils.widgets.get("archivo") or archivos[0]
print(f"Leyendo: {ruta}/{archivo}")

# COMMAND ----------

df = leer_exportacion(f"{ruta}/{archivo}", permitir_truncado=True)
print("¿Truncado?:", df.attrs["truncado"])
display(df.head(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Resumen

# COMMAND ----------

print(f"Registros: {len(df):,} | Columnas: {len(df.columns)}")
print(f"Meses: {df.fecha.min():%Y-%m} a {df.fecha.max():%Y-%m}")
for col in ["nivel_ingresos", "nivel_canasta", "ciudad"]:
    valores = sorted(df[col].dropna().unique())
    print(f"- {col}: {len(valores)} -> {valores}")
display(
    df.pivot_table(index="ciudad", columns="nivel_canasta", values="numero_indice", aggfunc="count")
)

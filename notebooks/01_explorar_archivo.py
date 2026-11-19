# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Explorar un archivo exportado
# MAGIC
# MAGIC Lee uno de los archivos que subiste al volumen y muestra su estructura.
# MAGIC Con esto diseñaremos las tablas `silver` y `gold` en la etapa 2.
# MAGIC
# MAGIC 1. Sube un archivo exportado de appindices a `/Volumes/ipc/bronze/raw/mensual/` (ver `docs/06`).
# MAGIC 2. Corre todas las celdas (**Run all**).
# MAGIC 3. Copia el resultado de la celda "Resumen" y compártelo.

# COMMAND ----------

# MAGIC %pip install openpyxl --quiet

# COMMAND ----------

dbutils.widgets.text("catalogo", "ipc", "Catálogo")
dbutils.widgets.text("carpeta", "mensual", "Subcarpeta del volumen")
catalogo = dbutils.widgets.get("catalogo")
carpeta = dbutils.widgets.get("carpeta")

ruta = f"/Volumes/{catalogo}/bronze/raw/{carpeta}"
archivos = [f for f in dbutils.fs.ls(ruta) if f.name.lower().endswith((".xlsx", ".csv"))]
display(archivos)
assert archivos, f"No hay archivos .xlsx/.csv en {ruta}. Sube uno primero (docs/06)."

# COMMAND ----------

import pandas as pd

archivo = archivos[0].path.replace("dbfs:", "")
print(f"Leyendo: {archivo}")

if archivo.lower().endswith(".csv"):
    df = pd.read_csv(archivo, sep=None, engine="python", encoding="utf-8-sig")
else:
    # La exportación de Power BI trae 2 filas de encabezado (medidas y dimensiones) y un pie
    # con "Filtros aplicados" (y un aviso si se truncó). Usamos la segunda fila como encabezado.
    crudo = pd.read_excel(archivo, header=None, dtype=str)
    print("\n".join(crudo.iloc[-3:, 0].dropna()))  # pie del archivo
    df = pd.read_excel(archivo, header=1, dtype=str)
    df = df[df["Año"].str.fullmatch(r"\d{4}", na=False)]

display(df.head(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Resumen

# COMMAND ----------

print(f"Filas: {len(df):,} | Columnas: {len(df.columns)}")
print("\nColumnas y tipos:")
print(df.dtypes.to_string())
print("\nValores distintos por columna (máx. 10 de ejemplo):")
for col in df.columns:
    valores = df[col].dropna().unique()
    print(f"- {col}: {len(valores)} distintos -> {list(valores[:10])}")

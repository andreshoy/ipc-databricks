# Databricks notebook source
# MAGIC %md
# MAGIC # 10 · Bronze: ingesta de archivos
# MAGIC
# MAGIC Lee los `.xlsx` de `/Volumes/ipc/bronze/raw/{historico,mensual}` y los guarda en la tabla
# MAGIC Delta **`ipc.bronze.ipc_indices`**: una fila por registro, tal como viene del DANE, más dos
# MAGIC columnas de auditoría (`archivo_origen`, `cargado_en`).
# MAGIC
# MAGIC **Es incremental:** la tabla **`ipc.bronze.archivos_cargados`** registra qué archivo se cargó
# MAGIC y cuándo. Si vuelves a correr el notebook, solo procesa archivos nuevos o modificados.
# MAGIC Los archivos truncados se registran como `rechazado` y no entran a la tabla.
# MAGIC
# MAGIC Conceptos que se practican: tablas Delta, `saveAsTable`, modo `append`, esquema explícito.

# COMMAND ----------

# MAGIC %pip install openpyxl --quiet

# COMMAND ----------

import os
import sys
from datetime import datetime, UTC

import pandas as pd
from pyspark.sql import types as T

sys.path.insert(0, os.path.abspath("../src"))
from ipc.lector import ExportacionTruncada, leer_exportacion
from ipc.transformaciones import COLUMNAS_BRONZE, preparar_bronze

dbutils.widgets.text("catalogo", "ipc", "Catálogo")
CAT = dbutils.widgets.get("catalogo")
RAW = f"/Volumes/{CAT}/bronze/raw"
TABLA = f"{CAT}.bronze.ipc_indices"
CONTROL = f"{CAT}.bronze.archivos_cargados"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Tablas (se crean solo la primera vez)

# COMMAND ----------

texto = T.StringType()
ESQUEMA = T.StructType(
    [
        T.StructField("fecha", T.DateType()),
        T.StructField("anio", T.IntegerType()),
        T.StructField("mes", T.IntegerType()),
        *[
            T.StructField(c, texto)
            for c in COLUMNAS_BRONZE
            if c not in ("fecha", "anio", "mes", "numero_indice", "cargado_en")
        ],
        T.StructField("numero_indice", T.DoubleType()),
        T.StructField("cargado_en", T.TimestampType()),
    ]
)
# Mismo orden que COLUMNAS_BRONZE
ESQUEMA = T.StructType([ESQUEMA[c] for c in COLUMNAS_BRONZE])

spark.createDataFrame([], ESQUEMA).write.mode("ignore").saveAsTable(TABLA)
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {CONTROL} (
        ruta STRING, archivo STRING, carpeta STRING, modificado TIMESTAMP,
        estado STRING, registros BIGINT, detalle STRING, cargado_en TIMESTAMP
    )
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. ¿Qué archivos son nuevos?

# COMMAND ----------

archivos = []
for carpeta in ["historico", "mensual"]:
    for f in sorted(os.listdir(f"{RAW}/{carpeta}")):
        if f.lower().endswith(".xlsx"):
            ruta = f"{RAW}/{carpeta}/{f}"
            modificado = datetime.fromtimestamp(os.path.getmtime(ruta), UTC)
            archivos.append((ruta, f, carpeta, modificado.replace(tzinfo=None)))

ya_cargados = {
    (r.ruta, r.modificado)
    for r in spark.table(CONTROL).where("estado = 'cargado'").select("ruta", "modificado").collect()
}
nuevos = [a for a in archivos if (a[0], a[3]) not in ya_cargados]
print(f"Archivos en el volumen: {len(archivos)} | nuevos o modificados: {len(nuevos)}")
for a in nuevos:
    print("  -", a[2], a[1])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Cargar los nuevos

# COMMAND ----------

control = []
for ruta, archivo, carpeta, modificado in nuevos:
    ahora = datetime.now(UTC).replace(tzinfo=None)
    try:
        pdf = preparar_bronze(leer_exportacion(ruta), archivo, pd.Timestamp(ahora))
        pdf["fecha"] = pdf["fecha"].dt.date
        pdf[["anio", "mes"]] = pdf[["anio", "mes"]].astype("int32")
        (spark.createDataFrame(pdf, ESQUEMA).write.mode("append").saveAsTable(TABLA))
        estado, registros, detalle = "cargado", len(pdf), ""
    except ExportacionTruncada as e:
        estado, registros, detalle = "rechazado", 0, str(e)
    except Exception as e:  # noqa: BLE001 - se registra cualquier error y se sigue
        estado, registros, detalle = "error", 0, repr(e)[:500]
    print(f"{estado:9s} {registros:>8,}  {carpeta}/{archivo} {detalle}")
    control.append((ruta, archivo, carpeta, modificado, estado, registros, detalle, ahora))

if control:
    spark.createDataFrame(control, spark.table(CONTROL).schema).write.mode("append").saveAsTable(
        CONTROL
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Resultado

# COMMAND ----------

display(spark.sql(f"SELECT * FROM {CONTROL} ORDER BY cargado_en DESC, archivo"))
display(
    spark.sql(f"""
        SELECT archivo_origen, count(*) AS registros, min(fecha) AS desde, max(fecha) AS hasta
        FROM {TABLA} GROUP BY archivo_origen ORDER BY archivo_origen
    """)
)

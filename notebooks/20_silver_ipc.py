# Databricks notebook source
# MAGIC %md
# MAGIC # 20 · Silver: IPC consolidado
# MAGIC
# MAGIC Construye **`ipc.silver.ipc_indices`** a partir de bronze:
# MAGIC
# MAGIC - Una fila por **serie y mes**. La serie es nivel de ingreso × ciudad × nivel de canasta ×
# MAGIC   código. Si un dato llegó en varios archivos, **gana la carga más reciente**.
# MAGIC - Columna `dominio`: `geografico` (oficial: Total de ingresos por ciudad), `ingresos` (oficial:
# MAGIC   nacional por nivel de ingreso) o `consulta` (ciudad × ingreso, no oficial).
# MAGIC - Agrega **dic-2018 = 100** (base del IPC 2018) a cada serie.
# MAGIC
# MAGIC También carga los **ponderadores** de `raw/referencia/` en tablas silver y corre las
# MAGIC **validaciones** de calidad.
# MAGIC
# MAGIC Se reconstruye completa en cada corrida (`overwrite`): son ~600 mil filas, así que es
# MAGIC rápido y más simple que un `MERGE`.

# COMMAND ----------

# MAGIC %pip install openpyxl --quiet

# COMMAND ----------

import glob
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.abspath("../src"))
from ipc.transformaciones import construir_silver, validar
from ipc.verificacion import indices_oficiales

dbutils.widgets.text("catalogo", "ipc", "Catálogo")
CAT = dbutils.widgets.get("catalogo")
REF = f"/Volumes/{CAT}/bronze/raw/referencia"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Consolidar

# COMMAND ----------

bronze = spark.table(f"{CAT}.bronze.ipc_indices").toPandas()
print(f"Bronze: {len(bronze):,} registros de {bronze.archivo_origen.nunique()} archivos")

silver = construir_silver(bronze)
print(f"Silver: {len(silver):,} registros")
display(silver.groupby(["dominio", "nivel_ingresos"]).size().rename("registros").reset_index())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Validaciones (deben salir todas ✅)

# COMMAND ----------

anexos = sorted(glob.glob(f"{REF}/anex-IPC-Indices-*.xlsx"))
oficiales = indices_oficiales(anexos[-1]) if anexos else None
checks = validar(silver, oficiales)
display(checks)
assert (checks.resultado == "✅").all(), "Hay validaciones fallidas: revisa la tabla de arriba"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Guardar

# COMMAND ----------

silver["fecha"] = silver["fecha"].dt.date
silver[["anio", "mes"]] = silver[["anio", "mes"]].astype("int32")

# Se envía a Spark por año para no mandar un bloque gigante de una vez:
# el primer año reemplaza la tabla (overwrite) y los demás se agregan (append).
for i, (anio, parte) in enumerate(silver.groupby("anio")):
    modo = "overwrite" if i == 0 else "append"
    (
        spark.createDataFrame(parte)
        .write.mode(modo)
        .option("overwriteSchema", "true")
        .saveAsTable(f"{CAT}.silver.ipc_indices")
    )
    print(f"{anio}: {len(parte):,} registros ({modo})")
spark.sql(f"""
    COMMENT ON TABLE {CAT}.silver.ipc_indices IS
    'IPC base dic-2018=100 (DANE) por serie y mes. Una fila por fecha x nivel_ingresos x ciudad x
     nivel_canasta x codigo. dominio: geografico | ingresos (oficiales) | consulta.'
""")

for nombre in ["subclase", "division", "ciudad"]:
    pdf = pd.read_csv(f"{REF}/ponderadores_{nombre}.csv", dtype=str)
    for c in pdf.columns:
        if c in ("pobres", "vulnerables", "clase_media", "altos", "total", "peso"):
            pdf[c] = pdf[c].astype(float)
    spark.createDataFrame(pdf).write.mode("overwrite").option(
        "overwriteSchema", "true"
    ).saveAsTable(f"{CAT}.silver.ponderadores_{nombre}")
    print(f"{CAT}.silver.ponderadores_{nombre}: {len(pdf)} filas")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Explorar con SQL
# MAGIC Una vez guardada, la tabla se consulta con SQL desde aquí o desde el **SQL Editor**.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- IPC nacional por nivel de ingreso: variación anual de los últimos 6 meses
# MAGIC WITH t AS (
# MAGIC   SELECT fecha, nivel_ingresos, numero_indice,
# MAGIC          LAG(numero_indice, 12) OVER (PARTITION BY nivel_ingresos ORDER BY fecha) AS hace_12m
# MAGIC   FROM ipc.silver.ipc_indices
# MAGIC   WHERE ciudad = 'NACIONAL' AND nivel_canasta = 'Total'
# MAGIC )
# MAGIC SELECT fecha, nivel_ingresos, numero_indice,
# MAGIC        ROUND(100 * (numero_indice / hace_12m - 1), 2) AS variacion_anual
# MAGIC FROM t
# MAGIC WHERE fecha >= add_months((SELECT max(fecha) FROM t), -5)
# MAGIC ORDER BY fecha DESC, nivel_ingresos

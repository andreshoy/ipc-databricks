# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Setup del catálogo
# MAGIC
# MAGIC Crea la estructura de **Unity Catalog** del proyecto (arquitectura *medallion*):
# MAGIC
# MAGIC | Objeto | Para qué sirve |
# MAGIC |---|---|
# MAGIC | `ipc` (catálogo) | Agrupa todo el proyecto |
# MAGIC | `ipc.bronze` | Datos crudos, tal como llegan del DANE |
# MAGIC | `ipc.silver` | Datos limpios, tipados y sin duplicados |
# MAGIC | `ipc.gold` | Tablas agregadas listas para los tableros |
# MAGIC | `ipc.bronze.raw` (volumen) | Carpeta donde subes los archivos exportados |
# MAGIC
# MAGIC Se puede correr varias veces sin problema (`IF NOT EXISTS`).
# MAGIC
# MAGIC **Si falla la creación del catálogo** (permisos), cambia el widget `catalogo` a `workspace`
# MAGIC y vuelve a correr todo.

# COMMAND ----------

dbutils.widgets.text("catalogo", "ipc", "Catálogo")
catalogo = dbutils.widgets.get("catalogo")
print(f"Usando catálogo: {catalogo}")

# COMMAND ----------

if catalogo != "workspace":
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalogo} COMMENT 'IPC Colombia base 2018 - DANE'")

for esquema, comentario in [
    ("bronze", "Datos crudos exportados de appindices.dane.gov.co"),
    ("silver", "IPC limpio y consolidado desde 2018"),
    ("gold", "Tablas para tableros de consulta y resumen"),
]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalogo}.{esquema} COMMENT '{comentario}'")

spark.sql(
    f"CREATE VOLUME IF NOT EXISTS {catalogo}.bronze.raw COMMENT 'Archivos xlsx/csv exportados'"
)

# COMMAND ----------

# Subcarpetas del volumen: histórico (carga inicial por tramos) y mensual (cada nuevo mes)
for carpeta in ["historico", "mensual"]:
    dbutils.fs.mkdirs(f"/Volumes/{catalogo}/bronze/raw/{carpeta}")

display(dbutils.fs.ls(f"/Volumes/{catalogo}/bronze/raw"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verificación
# MAGIC Deberías ver los tres esquemas abajo. También puedes abrirlos en **Catalog** (menú izquierdo).

# COMMAND ----------

display(spark.sql(f"SHOW SCHEMAS IN {catalogo}"))

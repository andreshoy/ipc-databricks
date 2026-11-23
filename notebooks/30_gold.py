# Databricks notebook source
# MAGIC %md
# MAGIC # 30 · Gold: tablas para los tableros
# MAGIC
# MAGIC A partir de `ipc.silver.ipc_indices` crea, **todo con SQL**:
# MAGIC
# MAGIC | Objeto | Tipo | Para qué |
# MAGIC |---|---|---|
# MAGIC | `gold.ipc_consulta` | tabla | Serie completa con variación mensual, anual y año corrido. Base del tablero de consulta. |
# MAGIC | `gold.contribuciones` | tabla | Cuánto aporta cada división y subclase a la inflación nacional (por nivel de ingreso). |
# MAGIC | `gold.brechas` | tabla | Diferencia de inflación: cada nivel de ingreso vs. total y cada ciudad vs. nacional. |
# MAGIC | `gold.resumen_kpi` | vista | Indicadores del último mes. |
# MAGIC | `gold.resumen_ranking` | vista | Subclases que más subieron/bajaron y más aportaron en el último mes. |
# MAGIC | `gold.resumen_brechas` | vista | Brechas del último mes y su cambio. |
# MAGIC
# MAGIC Conceptos que se practican: `CREATE OR REPLACE TABLE ... AS SELECT`, CTE (`WITH`), funciones
# MAGIC de ventana (`LAG`, `ROW_NUMBER`), `UNPIVOT` y **vistas** (se recalculan solas al consultarlas,
# MAGIC así que el "último mes" siempre es el más reciente sin volver a correr nada).

# COMMAND ----------

dbutils.widgets.text("catalogo", "ipc", "Catálogo")
CAT = dbutils.widgets.get("catalogo")

# Desde aquí las celdas SQL usan nombres cortos (silver.x, gold.x) dentro de este catálogo
spark.sql(f"USE CATALOG {CAT}")
print("Catálogo en uso:", spark.sql("SELECT current_catalog()").first()[0])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. `gold.ipc_consulta`
# MAGIC
# MAGIC `LAG(x, 12) OVER w` trae el valor de 12 filas atrás **dentro de la misma serie** (la ventana
# MAGIC `w` parte por serie y ordena por fecha). Como protección, solo se usa si esa fila es
# MAGIC exactamente de 12 meses antes; si faltara un mes, la variación queda en `NULL` en vez de salir
# MAGIC mal calculada.
# MAGIC
# MAGIC El **año corrido** compara con diciembre del año anterior, así que se une con esas filas.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE gold.ipc_consulta
# MAGIC COMMENT 'IPC base dic-2018=100 con variaciones (%). Una fila por fecha x nivel_ingresos x ciudad x nivel_canasta x codigo.'
# MAGIC AS
# MAGIC WITH con_rezagos AS (
# MAGIC   SELECT
# MAGIC     *,
# MAGIC     IF(LAG(fecha, 1)  OVER w = add_months(fecha, -1),  LAG(numero_indice, 1)  OVER w, NULL) AS indice_mes_anterior,
# MAGIC     IF(LAG(fecha, 12) OVER w = add_months(fecha, -12), LAG(numero_indice, 12) OVER w, NULL) AS indice_hace_12_meses
# MAGIC   FROM silver.ipc_indices
# MAGIC   WINDOW w AS (PARTITION BY nivel_ingresos, ciudad, nivel_canasta, codigo ORDER BY fecha)
# MAGIC ),
# MAGIC diciembres AS (
# MAGIC   SELECT nivel_ingresos, ciudad, nivel_canasta, codigo, anio + 1 AS anio, numero_indice AS indice_dic_anterior
# MAGIC   FROM silver.ipc_indices
# MAGIC   WHERE mes = 12
# MAGIC )
# MAGIC SELECT
# MAGIC   c.fecha, c.anio, c.mes,
# MAGIC   c.dominio,
# MAGIC   c.dominio IN ('geografico', 'ingresos') AS es_oficial,
# MAGIC   c.nivel_ingresos,
# MAGIC   CASE c.nivel_ingresos
# MAGIC     WHEN 'Total Nivel de Ingresos' THEN 0 WHEN 'Pobres' THEN 1 WHEN 'Vulnerables' THEN 2
# MAGIC     WHEN 'Clase Media' THEN 3 WHEN 'Ingresos Altos' THEN 4
# MAGIC   END AS orden_ingreso,
# MAGIC   c.ciudad,
# MAGIC   c.nivel_canasta,
# MAGIC   CASE c.nivel_canasta
# MAGIC     WHEN 'Total' THEN 0 WHEN 'Division' THEN 1 WHEN 'Grupo' THEN 2 WHEN 'Clase' THEN 3 WHEN 'Subclase' THEN 4
# MAGIC   END AS orden_canasta,
# MAGIC   c.codigo, c.nombre,
# MAGIC   c.division_codigo, c.division_nombre,
# MAGIC   c.grupo_codigo, c.grupo_nombre,
# MAGIC   c.clase_codigo, c.clase_nombre,
# MAGIC   c.numero_indice,
# MAGIC   100 * (c.numero_indice / c.indice_mes_anterior - 1)  AS variacion_mensual,
# MAGIC   100 * (c.numero_indice / c.indice_hace_12_meses - 1) AS variacion_anual,
# MAGIC   100 * (c.numero_indice / d.indice_dic_anterior - 1)  AS variacion_anio_corrido
# MAGIC FROM con_rezagos c
# MAGIC LEFT JOIN diciembres d
# MAGIC   USING (nivel_ingresos, ciudad, nivel_canasta, codigo, anio)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. `gold.contribuciones`
# MAGIC
# MAGIC La **contribución** de un rubro es cuántos puntos porcentuales (p.p.) de la inflación total
# MAGIC explica. Con el peso `w` del rubro (en %, de los ponderadores del DANE):
# MAGIC
# MAGIC `contribución anual = w × (índice rubro hoy − índice rubro hace 12 meses) / índice total hace 12 meses`
# MAGIC
# MAGIC Las contribuciones de las 12 divisiones (o de las 188 subclases) suman la variación del total.
# MAGIC Solo se calcula para el **nacional** porque el DANE no publica pesos por ciudad × subclase.
# MAGIC
# MAGIC Las tablas de ponderadores tienen una columna por nivel de ingreso (`pobres`, `altos`, ...).
# MAGIC `UNPIVOT` las convierte en filas para poder cruzarlas con la serie.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE gold.contribuciones
# MAGIC COMMENT 'Contribución (p.p.) de cada división y subclase a la inflación nacional, por nivel de ingreso.'
# MAGIC AS
# MAGIC WITH pesos_columnas AS (
# MAGIC   SELECT 'Division' AS nivel_canasta, division_codigo AS codigo, pobres, vulnerables, clase_media, altos, total
# MAGIC   FROM silver.ponderadores_division
# MAGIC   UNION ALL
# MAGIC   SELECT 'Subclase', subclase_codigo, pobres, vulnerables, clase_media, altos, total
# MAGIC   FROM silver.ponderadores_subclase
# MAGIC ),
# MAGIC pesos AS (
# MAGIC   SELECT
# MAGIC     nivel_canasta, codigo, peso,
# MAGIC     CASE columna
# MAGIC       WHEN 'pobres' THEN 'Pobres' WHEN 'vulnerables' THEN 'Vulnerables'
# MAGIC       WHEN 'clase_media' THEN 'Clase Media' WHEN 'altos' THEN 'Ingresos Altos'
# MAGIC       WHEN 'total' THEN 'Total Nivel de Ingresos'
# MAGIC     END AS nivel_ingresos
# MAGIC   FROM pesos_columnas
# MAGIC   UNPIVOT (peso FOR columna IN (pobres, vulnerables, clase_media, altos, total))
# MAGIC ),
# MAGIC nacional AS (
# MAGIC   SELECT
# MAGIC     fecha, anio, mes, nivel_ingresos, orden_ingreso, nivel_canasta, codigo, nombre,
# MAGIC     division_codigo, division_nombre, numero_indice, variacion_mensual, variacion_anual,
# MAGIC     numero_indice / (1 + variacion_mensual / 100) AS indice_mes_anterior,
# MAGIC     numero_indice / (1 + variacion_anual / 100)   AS indice_hace_12_meses
# MAGIC   FROM gold.ipc_consulta
# MAGIC   WHERE ciudad = 'NACIONAL'
# MAGIC ),
# MAGIC total AS (
# MAGIC   SELECT fecha, nivel_ingresos,
# MAGIC          indice_mes_anterior  AS total_mes_anterior,
# MAGIC          indice_hace_12_meses AS total_hace_12_meses,
# MAGIC          variacion_mensual    AS total_variacion_mensual,
# MAGIC          variacion_anual      AS total_variacion_anual
# MAGIC   FROM nacional
# MAGIC   WHERE nivel_canasta = 'Total'
# MAGIC )
# MAGIC SELECT
# MAGIC   n.fecha, n.anio, n.mes, n.nivel_ingresos, n.orden_ingreso, n.nivel_canasta,
# MAGIC   n.codigo, n.nombre, n.division_codigo, n.division_nombre,
# MAGIC   p.peso,
# MAGIC   n.numero_indice, n.variacion_mensual, n.variacion_anual,
# MAGIC   p.peso * (n.numero_indice - n.indice_mes_anterior)  / t.total_mes_anterior  AS contribucion_mensual,
# MAGIC   p.peso * (n.numero_indice - n.indice_hace_12_meses) / t.total_hace_12_meses AS contribucion_anual,
# MAGIC   t.total_variacion_mensual, t.total_variacion_anual
# MAGIC FROM nacional n
# MAGIC JOIN pesos p USING (nivel_canasta, codigo, nivel_ingresos)
# MAGIC JOIN total t USING (fecha, nivel_ingresos)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. `gold.brechas`
# MAGIC
# MAGIC Una **brecha** es la diferencia en p.p. entre la inflación anual de un grupo y la de su
# MAGIC referencia. Hay tres tipos:
# MAGIC
# MAGIC - `ingreso`: cada nivel de ingreso vs. el total nacional (dominio oficial).
# MAGIC - `pobres_vs_altos`: Pobres vs. Ingresos Altos (la brecha clásica).
# MAGIC - `ciudad`: cada ciudad vs. el nacional (Total de ingresos, dominio oficial).
# MAGIC
# MAGIC Se calcula para el Total y para las 12 divisiones. Con `LAG` también se ve si la brecha se
# MAGIC abrió o se cerró frente al mes anterior y frente al mismo mes del año pasado.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE gold.brechas
# MAGIC COMMENT 'Brechas de inflación (p.p.): ingreso vs total, pobres vs altos y ciudad vs nacional.'
# MAGIC AS
# MAGIC WITH base AS (
# MAGIC   SELECT fecha, nivel_ingresos, ciudad, nivel_canasta, codigo, nombre, variacion_mensual, variacion_anual
# MAGIC   FROM gold.ipc_consulta
# MAGIC   WHERE es_oficial AND nivel_canasta IN ('Total', 'Division')
# MAGIC ),
# MAGIC nacional_total AS (
# MAGIC   SELECT * FROM base WHERE ciudad = 'NACIONAL' AND nivel_ingresos = 'Total Nivel de Ingresos'
# MAGIC ),
# MAGIC pares AS (
# MAGIC   -- Cada nivel de ingreso vs. total nacional
# MAGIC   SELECT 'ingreso' AS tipo, g.fecha, g.nivel_canasta, g.codigo, g.nombre,
# MAGIC          g.nivel_ingresos AS grupo, 'Total Nivel de Ingresos' AS referencia,
# MAGIC          g.variacion_mensual AS vm_grupo, r.variacion_mensual AS vm_ref,
# MAGIC          g.variacion_anual   AS va_grupo, r.variacion_anual   AS va_ref
# MAGIC   FROM base g JOIN nacional_total r USING (fecha, nivel_canasta, codigo)
# MAGIC   WHERE g.ciudad = 'NACIONAL' AND g.nivel_ingresos <> 'Total Nivel de Ingresos'
# MAGIC   UNION ALL
# MAGIC   -- Pobres vs. Ingresos Altos
# MAGIC   SELECT 'pobres_vs_altos', g.fecha, g.nivel_canasta, g.codigo, g.nombre,
# MAGIC          'Pobres', 'Ingresos Altos',
# MAGIC          g.variacion_mensual, r.variacion_mensual, g.variacion_anual, r.variacion_anual
# MAGIC   FROM base g JOIN base r USING (fecha, ciudad, nivel_canasta, codigo)
# MAGIC   WHERE g.ciudad = 'NACIONAL' AND g.nivel_ingresos = 'Pobres' AND r.nivel_ingresos = 'Ingresos Altos'
# MAGIC   UNION ALL
# MAGIC   -- Cada ciudad vs. nacional
# MAGIC   SELECT 'ciudad', g.fecha, g.nivel_canasta, g.codigo, g.nombre,
# MAGIC          g.ciudad, 'NACIONAL',
# MAGIC          g.variacion_mensual, r.variacion_mensual, g.variacion_anual, r.variacion_anual
# MAGIC   FROM base g JOIN nacional_total r USING (fecha, nivel_canasta, codigo)
# MAGIC   WHERE g.ciudad <> 'NACIONAL' AND g.nivel_ingresos = 'Total Nivel de Ingresos'
# MAGIC ),
# MAGIC con_brecha AS (
# MAGIC   SELECT *, va_grupo - va_ref AS brecha_anual, vm_grupo - vm_ref AS brecha_mensual
# MAGIC   FROM pares
# MAGIC )
# MAGIC SELECT
# MAGIC   tipo, fecha, year(fecha) AS anio, month(fecha) AS mes, nivel_canasta, codigo, nombre, grupo, referencia,
# MAGIC   va_grupo AS variacion_anual_grupo, va_ref AS variacion_anual_referencia, brecha_anual,
# MAGIC   vm_grupo AS variacion_mensual_grupo, vm_ref AS variacion_mensual_referencia, brecha_mensual,
# MAGIC   brecha_anual - IF(LAG(fecha, 1)  OVER w = add_months(fecha, -1),  LAG(brecha_anual, 1)  OVER w, NULL)
# MAGIC     AS cambio_brecha_vs_mes_anterior,
# MAGIC   brecha_anual - IF(LAG(fecha, 12) OVER w = add_months(fecha, -12), LAG(brecha_anual, 12) OVER w, NULL)
# MAGIC     AS cambio_brecha_vs_anio_anterior
# MAGIC FROM con_brecha
# MAGIC WINDOW w AS (PARTITION BY tipo, grupo, nivel_canasta, codigo ORDER BY fecha)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Vistas del último mes
# MAGIC
# MAGIC Una **vista** guarda la consulta, no los datos: cada vez que el tablero la lee, Databricks la
# MAGIC ejecuta sobre las tablas de arriba. Por eso `MAX(fecha)` siempre apunta al mes más reciente.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW gold.resumen_kpi
# MAGIC COMMENT 'Último mes: índice y variaciones del total nacional por nivel de ingreso.'
# MAGIC AS
# MAGIC WITH serie AS (
# MAGIC   SELECT fecha, nivel_ingresos, orden_ingreso, numero_indice,
# MAGIC          variacion_mensual, variacion_anual, variacion_anio_corrido,
# MAGIC          LAG(variacion_anual, 1)  OVER w AS variacion_anual_mes_anterior,
# MAGIC          LAG(variacion_anual, 12) OVER w AS variacion_anual_hace_un_anio
# MAGIC   FROM gold.ipc_consulta
# MAGIC   WHERE ciudad = 'NACIONAL' AND nivel_canasta = 'Total'
# MAGIC   WINDOW w AS (PARTITION BY nivel_ingresos ORDER BY fecha)
# MAGIC )
# MAGIC SELECT *, variacion_anual - variacion_anual_mes_anterior AS cambio_anual_vs_mes_anterior
# MAGIC FROM serie
# MAGIC WHERE fecha = (SELECT MAX(fecha) FROM gold.ipc_consulta);
# MAGIC
# MAGIC CREATE OR REPLACE VIEW gold.resumen_ranking
# MAGIC COMMENT 'Último mes, nacional: subclases con su variación, contribución y posición en cada ranking.'
# MAGIC AS
# MAGIC SELECT
# MAGIC   fecha, nivel_ingresos, orden_ingreso, codigo, nombre, division_nombre, peso,
# MAGIC   variacion_mensual, variacion_anual, contribucion_mensual, contribucion_anual,
# MAGIC   100 * contribucion_anual / total_variacion_anual AS participacion_anual,
# MAGIC   ROW_NUMBER() OVER (PARTITION BY nivel_ingresos ORDER BY variacion_mensual DESC)   AS rank_mayor_alza_mensual,
# MAGIC   ROW_NUMBER() OVER (PARTITION BY nivel_ingresos ORDER BY variacion_mensual ASC)    AS rank_mayor_baja_mensual,
# MAGIC   ROW_NUMBER() OVER (PARTITION BY nivel_ingresos ORDER BY variacion_anual DESC)     AS rank_mayor_alza_anual,
# MAGIC   ROW_NUMBER() OVER (PARTITION BY nivel_ingresos ORDER BY contribucion_anual DESC)  AS rank_mayor_contribucion_anual
# MAGIC FROM gold.contribuciones
# MAGIC WHERE nivel_canasta = 'Subclase'
# MAGIC   AND fecha = (SELECT MAX(fecha) FROM gold.contribuciones);
# MAGIC
# MAGIC CREATE OR REPLACE VIEW gold.resumen_brechas
# MAGIC COMMENT 'Último mes: brechas de inflación y su cambio frente al mes anterior y al año anterior.'
# MAGIC AS
# MAGIC SELECT *
# MAGIC FROM gold.brechas
# MAGIC WHERE fecha = (SELECT MAX(fecha) FROM gold.brechas);

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Validaciones (deben salir todas ✅)
# MAGIC
# MAGIC Con los datos hasta oct-2026, la inflación anual nacional debe dar **6,30 %** (Pobres 6,34;
# MAGIC Vulnerables 6,39; Clase Media 6,33; Ingresos Altos 6,20) y las contribuciones deben sumar
# MAGIC casi exactamente la variación del total (la diferencia normal es ≤ 0,01 p.p.).

# COMMAND ----------

import pandas as pd

checks = []


def check(nombre, ok, detalle):
    checks.append({"chequeo": nombre, "resultado": "✅" if ok else "❌", "detalle": detalle})


filas = {
    t: spark.table(f"gold.{t}").count()
    for t in [
        "ipc_consulta",
        "contribuciones",
        "brechas",
        "resumen_kpi",
        "resumen_ranking",
        "resumen_brechas",
    ]
}
check("Todas las tablas y vistas tienen filas", all(filas.values()), str(filas))

n_silver = spark.table("silver.ipc_indices").count()
check(
    "ipc_consulta tiene las mismas filas que silver",
    filas["ipc_consulta"] == n_silver,
    f"{filas['ipc_consulta']:,} vs {n_silver:,}",
)

suma = spark.sql("""
    SELECT nivel_canasta, nivel_ingresos,
           MAX(ABS(suma_anual - total_variacion_anual)) AS dif_anual,
           MAX(ABS(suma_mensual - total_variacion_mensual)) AS dif_mensual
    FROM (
      SELECT fecha, nivel_canasta, nivel_ingresos,
             SUM(contribucion_anual) AS suma_anual, SUM(contribucion_mensual) AS suma_mensual,
             FIRST(total_variacion_anual) AS total_variacion_anual,
             FIRST(total_variacion_mensual) AS total_variacion_mensual
      FROM gold.contribuciones
      GROUP BY ALL
    )
    GROUP BY ALL
""").toPandas()
peor = suma[["dif_anual", "dif_mensual"]].max().max()
check("Contribuciones suman la variación total", peor < 0.05, f"diferencia máx {peor:.3f} p.p.")

n_sub = spark.sql("""
    SELECT COUNT(DISTINCT codigo) FROM gold.contribuciones
    WHERE nivel_canasta = 'Subclase' AND fecha = (SELECT MAX(fecha) FROM gold.contribuciones)
""").first()[0]
check("188 subclases con peso en el último mes", n_sub == 188, f"{n_sub} subclases")

display(pd.DataFrame(checks))
assert all(c["resultado"] == "✅" for c in checks), (
    "Hay validaciones fallidas: revisa la tabla de arriba"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Explorar el último mes

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT nivel_ingresos,
# MAGIC        ROUND(numero_indice, 2) AS indice,
# MAGIC        ROUND(variacion_mensual, 2) AS mensual,
# MAGIC        ROUND(variacion_anual, 2) AS anual,
# MAGIC        ROUND(variacion_anio_corrido, 2) AS anio_corrido,
# MAGIC        ROUND(cambio_anual_vs_mes_anterior, 2) AS cambio_anual_pp
# MAGIC FROM gold.resumen_kpi
# MAGIC ORDER BY orden_ingreso

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Las 10 subclases que más aportaron a la inflación anual (total nacional)
# MAGIC SELECT rank_mayor_contribucion_anual AS puesto, nombre,
# MAGIC        ROUND(variacion_anual, 2) AS variacion_anual,
# MAGIC        ROUND(contribucion_anual, 2) AS contribucion_pp,
# MAGIC        ROUND(participacion_anual, 1) AS participacion_pct
# MAGIC FROM gold.resumen_ranking
# MAGIC WHERE nivel_ingresos = 'Total Nivel de Ingresos' AND rank_mayor_contribucion_anual <= 10
# MAGIC ORDER BY puesto

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Brechas del último mes (Total de la canasta)
# MAGIC SELECT tipo, grupo, referencia,
# MAGIC        ROUND(brecha_anual, 2) AS brecha_pp,
# MAGIC        ROUND(cambio_brecha_vs_mes_anterior, 2) AS vs_mes_anterior,
# MAGIC        ROUND(cambio_brecha_vs_anio_anterior, 2) AS vs_anio_anterior
# MAGIC FROM gold.resumen_brechas
# MAGIC WHERE nivel_canasta = 'Total'
# MAGIC ORDER BY tipo, brecha_pp DESC

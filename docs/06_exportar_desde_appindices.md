# 06 · Exportar el IPC desde appindices y subirlo a Databricks

## Por qué este paso es manual

<https://appindices.dane.gov.co/> es un **reporte de Power BI embebido**: los datos se ven en
pantalla y se exportan con un botón, pero no hay una API ni enlaces directos a archivos. Además,
el cómputo de Databricks Free Edition solo puede salir a internet hacia algunos dominios de
confianza y no tiene navegador. Por eso:

- **Tú**: exportas el archivo y lo subes al volumen (≈5 minutos al mes).
- **Databricks**: detecta el archivo nuevo y hace todo lo demás (etapa 2).

Guía oficial del DANE: <https://appindices.dane.gov.co/resources/pdf/guia_de_usuario.pdf>

## Filtros a seleccionar en appindices

| Filtro | Selección |
|---|---|
| Año | El/los año(s) del tramo (ver abajo) |
| Mes | **Seleccionar todo** (o solo el mes nuevo en la actualización mensual) |
| Cobertura geográfica | **Total Nacional y Ciudades** |
| Ciudad | **Seleccionar todo** |
| Nivel de ingresos | **Seleccionar todo** (Total, Altos, Clase Media, Vulnerables, Pobres) |
| Nivel de canasta | **Total, División, Grupo, Clase, Subclase** (todos) |
| División / Grupo / Clase / Subclase | **Seleccionar todo** |
| Valor | **Número Índice** y **Variación Mensual, Año Corrido, Anual** |

Luego, sobre la tabla de resultados: menú **⋯** (arriba a la derecha de la tabla) →
**Exportar datos** → formato **.xlsx** (permite hasta 150.000 filas; el .csv solo 30.000).

## Cuántas filas salen y cómo partir el histórico

Estimación (por confirmar con tu primer archivo):
~39 geografías (nacional + 38 ciudades) × 5 niveles de ingreso × ~330 rubros (todos los niveles de
canasta) ≈ **64.000 filas por mes**.

- **Actualización mensual**: 1 mes ≈ 64.000 filas → **un solo archivo .xlsx**. ✔️
- **Carga histórica** (ene-2019 → hoy, ~95 meses ≈ 6 millones de filas): no cabe en una sola
  exportación. Opciones:
  1. **Recomendado para empezar**: exporta el histórico solo con nivel de canasta
     **Total + División** (≈ 39 × 5 × 13 × 12 ≈ 30.000 filas por año → un archivo por año o
     uno cada 4 años). Con eso ya funcionan los tableros por división de gasto.
  2. Para el detalle completo (subclase) histórico: exporta de a **2 meses** por archivo, o por
     año filtrando grupos de ciudades. Es tedioso pero se hace una sola vez; lo podemos hacer
     gradualmente.

  Si el filtro de Año no muestra 2018: el IPC base 2018 arranca en diciembre de 2018 (= 100) y la
  metodología nueva desde enero de 2019. Exporta lo que esté disponible.

Si la exportación supera el límite, Power BI corta en silencio o muestra un aviso: **verifica que
el último mes/ciudad esperado esté en el archivo**.

## Nombres de archivo (convención)

- Histórico: `historico/ipc_division_2019_2022.xlsx`, `historico/ipc_subclase_2024_01-02.xlsx`
- Mensual: `mensual/ipc_2026_10.xlsx` (año_mes de los datos, no de la descarga)

## Subir el archivo al volumen

**Opción 1 · Interfaz web**: **Catalog** → `ipc` → `bronze` → **Volumes** → `raw` → entra a la
carpeta `mensual` (o `historico`) → **Upload to this volume** → arrastra el archivo.

**Opción 2 · Terminal** (requiere el paso 04):

```bash
databricks fs cp ~/Downloads/ipc_2026_10.xlsx dbfs:/Volumes/ipc/bronze/raw/mensual/
databricks fs ls dbfs:/Volumes/ipc/bronze/raw/mensual
```

Los archivos no se suben a GitHub (están en `.gitignore`): los datos viven en Databricks.

## Explorar el primer archivo

Abre [notebooks/01_explorar_archivo.py](../notebooks/01_explorar_archivo.py) en Databricks y dale
**Run all**. La celda **Resumen** muestra columnas, tipos y valores de ejemplo.

## ✅ Checkpoint
Hay al menos un archivo en `/Volumes/ipc/bronze/raw/mensual/` y el notebook 01 muestra su resumen.
**Copia ese resumen y compártelo**: con él diseñamos las tablas silver y gold (etapa 2).

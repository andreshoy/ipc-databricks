# 06 · Exportar el IPC desde appindices y subirlo a Databricks

## Por qué este paso es manual

<https://appindices.dane.gov.co/> es un **reporte de Power BI embebido**: los datos se ven en
pantalla y se exportan con un botón, pero no hay una API ni enlaces directos a archivos. Además,
el cómputo de Databricks Free Edition solo puede salir a internet hacia algunos dominios de
confianza y no tiene navegador. Por eso:

- **Tú**: exportas el archivo y lo subes al volumen.
- **Databricks**: detecta el archivo nuevo y hace todo lo demás (etapa 2).

Guía oficial del DANE: <https://appindices.dane.gov.co/resources/pdf/guia_de_usuario.pdf>

## El query mensual

![Filtros del query mensual](img/pantallazo_query.jpeg)

| Filtro | Selección |
|---|---|
| Año / Mes | El mes nuevo (p. ej. 2026 / Oct) |
| Cobertura geográfica | Todas |
| Ciudad | Todas |
| Nivel de ingresos | **Uno a la vez** (ver límite abajo) |
| Nivel de canasta | Subclase |
| División / Grupo / Clase / Subclase | Todas |
| Valor a graficar | Ver recomendación abajo |

Luego, sobre la tabla: menú **⋯** → **Exportar datos** → **.xlsx**.

## Lo que trae el archivo (revisado con un ejemplo real)

- Hoja `Export`. Dos filas de encabezado: nombres de medidas y nombres de dimensiones.
- Columnas: Año, Mes, Nivel de ingresos, Nivel de canasta, División, Grupo, Clase, Subclase
  (como `01110100 - Arroz`: código + nombre), Cobertura Geografica (ciudad) y 15 medidas:
  Número Índice y Variación / Contribución / Participación (mensual, año corrido, anual,
  trimestral, semestral).
- Los números vienen como texto con coma decimal (`155,06`). Hay celdas vacías (no publicadas).
- **14 geografías**: Nacional + 13 ciudades (Barranquilla, Bogotá, Bucaramanga, Cali, Cartagena,
  Cúcuta, Manizales, Medellín, Montería, Neiva, Pasto, Pereira, Villavicencio). San Andrés y
  Quibdó vienen excluidas por el reporte.
- ~188 subclases por ciudad → **~2.630 filas por mes** por cada nivel de ingresos.
- Al final: "Filtros aplicados: ..." (útil como auditoría).

El lector [src/ipc/lector.py](../src/ipc/lector.py) ya entiende este formato.

## ⚠️ Límite real de exportación

Una exportación de un año completo **se cortó en ~9.400 filas** (enero a marzo completos y abril
a medias) y trajo al final el aviso:
`Exported data exceeded the allowed volume. Some data may have been omitted.`

El lector rechaza archivos con ese aviso, así que no se cuelan datos incompletos.

**Cómo exportar sin pasarse** (con las 15 medidas, cada archivo admite ~3 meses):

| Exportación | Contenido | Filas aprox. | Archivos |
|---|---|---|---|
| Mensual | 1 mes × 1 nivel de ingresos | 2.630 | 5 por mes (uno por nivel de ingresos) |
| Histórico | 3 meses × 1 nivel de ingresos | 7.900 | 4 por año por nivel de ingresos |

> **Prueba sugerida**: el límite de Power BI puede depender del total de celdas y no solo de las
> filas. Exporta un año con *Valor a graficar* = solo **Número Índice, Variación Mensual,
> Variación Anual, Contribución Mensual y Contribución Anual** y revisa si llega diciembre. Si
> llega, el histórico se reduce mucho (un archivo por año por nivel de ingresos).

Prioridad para el histórico: primero **Total Nivel de Ingresos** (2019 → hoy); después los demás
niveles de ingresos, que son los que permiten analizar las brechas.

## Nombres de archivo (convención)

`ipc_<nivel>_<año>_<mesinicial>-<mesfinal>.xlsx`, con nivel en `total`, `altos`, `media`,
`vulnerables`, `pobres`:

- Histórico: `historico/ipc_total_2019_01-03.xlsx`
- Mensual: `mensual/ipc_total_2026_10.xlsx`, `mensual/ipc_pobres_2026_10.xlsx`

El nombre es solo para que tú te orientes: el proceso lee año, mes e ingreso del contenido del
archivo y elimina duplicados si un mes llega dos veces.

## Dónde guardar los archivos

| En tu computador (no se sube a GitHub) | En Databricks |
|---|---|
| `data/historico/` | `/Volumes/ipc/bronze/raw/historico/` |
| `data/mensual/` | `/Volumes/ipc/bronze/raw/mensual/` |

**Subir por la interfaz web**: **Catalog** → `ipc` → `bronze` → **Volumes** → `raw` → carpeta →
**Upload to this volume**.

**Subir por terminal** (requiere el paso 04), toda la carpeta de una vez:

```bash
databricks fs cp -r data/historico dbfs:/Volumes/ipc/bronze/raw/historico
databricks fs ls dbfs:/Volumes/ipc/bronze/raw/historico
```

## Explorar el primer archivo

Abre [notebooks/01_explorar_archivo.py](../notebooks/01_explorar_archivo.py) en Databricks y dale
**Run all** para confirmar que Databricks lee el archivo.

## ✅ Checkpoint
Hay archivos en `/Volumes/ipc/bronze/raw/` y el notebook 01 muestra su resumen.

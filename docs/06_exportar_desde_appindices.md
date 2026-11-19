# 06 · Exportar el IPC desde appindices y subirlo a Databricks

## Por qué este paso es manual

<https://appindices.dane.gov.co/> es un **reporte de Power BI embebido**: los datos se ven en
pantalla y se exportan con un botón, pero no hay una API ni enlaces directos a archivos. Además,
el cómputo de Databricks Free Edition solo puede salir a internet hacia algunos dominios de
confianza y no tiene navegador. Por eso:

- **Tú**: exportas los archivos y los subes al volumen.
- **Databricks**: detecta el archivo nuevo y hace todo lo demás (etapa 2).

Guía oficial del DANE: <https://appindices.dane.gov.co/resources/pdf/guia_de_usuario.pdf>

## Qué datos bajamos y por qué

El DANE difunde oficialmente dos "dominios" (ver [docs/08](08_metodologia_ponderadores.md)):

| Dominio oficial | Desagregación | Exportación |
|---|---|---|
| **Geográfico** | Nacional + ciudades × todos los niveles de canasta, para el Total de ingresos | **A · Ciudades** |
| **Nivel de ingreso** | Solo nacional × todos los niveles de canasta × Pobres, Vulnerables, Clase media, Altos | **B · Ingresos** |

Ciudad × nivel de ingreso **no** es un dominio oficial (la metodología lo descarta por tamaño de
muestra), así que no lo descargamos para el histórico.

¿Por qué los índices de subclase por ingreso? Si se usan los índices de subclase del Total con
los pesos de cada nivel de ingreso, la brecha sale mal (oct-2026: Pobres–Altos 0,11 pp en vez de
0,18 pp). Además, con las subclases por ingreso se puede explicar qué rubros abren o cierran la
brecha.

Siempre se exporta **solo `Número Índice`** y **todos los niveles de canasta** (Total, División,
Grupo, Clase, Subclase). Las variaciones se calculan del índice y las contribuciones con los
ponderadores.

## Histórico 2019 → 2026 (una sola vez, 10 archivos)

### A · Ciudades: 1 archivo por año (8 archivos)

| Filtro | Selección |
|---|---|
| Año | **Un año** (2019, 2020, … 2026) |
| Mes | Seleccionar todo |
| Cobertura geográfica | Todas |
| Ciudad | Todas |
| Nivel de ingresos | **Total Nivel de Ingresos** |
| Nivel de canasta | Total, División, Grupo, Clase, Subclase |
| División / Grupo / Clase / Subclase | Todas |
| Valor a graficar | Solo **Número Índice** (desmarca "Seleccionar todo") |

~94.000 filas por archivo (327 rubros × 24 geografías × 12 meses). Nombre:
`ipc_ciudades_2019.xlsx` … `ipc_ciudades_2026.xlsx`.

### B · Ingresos nacional: 2 archivos de 4 años

| Filtro | Selección |
|---|---|
| Año | **2019, 2020, 2021, 2022** (segundo archivo: 2023–2026) |
| Mes | Seleccionar todo |
| Cobertura geográfica | **Total Nacional** |
| Nivel de ingresos | Pobres, Vulnerables, Clase Media, Ingresos Altos |
| Nivel de canasta | Total, División, Grupo, Clase, Subclase |
| División / Grupo / Clase / Subclase | Todas |
| Valor a graficar | Solo **Número Índice** |

~63.000 filas por archivo (327 rubros × 4 ingresos × 48 meses). Nombre:
`ipc_ingresos_2019_2022.xlsx` y `ipc_ingresos_2023_2026.xlsx`.

### Sobre 2018
La base es **diciembre de 2018 = 100** para todas las series, así que el histórico consolidado
arranca con dic-2018 = 100 (lo genera el proceso) y datos reales desde enero de 2019. Si el filtro
de Año ofrece 2018, exporta también ese año con los dos esquemas y lo revisamos.

## Actualización mensual (1 archivo)

| Filtro | Selección |
|---|---|
| Año / Mes | El mes nuevo (p. ej. 2026 / Oct) |
| Cobertura geográfica / Ciudad | Todas |
| Nivel de ingresos | Seleccionar todo |
| Nivel de canasta | Todos |
| División / Grupo / Clase / Subclase | Todas |
| Valor a graficar | Solo **Número Índice** |

~39.000 filas. Nombre: `ipc_2026_10.xlsx`. Trae de más la combinación ciudad × ingreso; el
proceso la marca como "no oficial" y conserva los dos dominios oficiales.

## Cómo exportar

Sobre la tabla de resultados: menú **⋯** (arriba a la derecha) → **Exportar datos** → **.xlsx**.

![Filtros del query](img/pantallazo_query.jpeg)

**Verifica cada archivo** abriéndolo en Excel. Las primeras filas deben decir:
- ✅ `Medida es Número Índice` en "Filtros aplicados".
- ❌ No debe aparecer `Exported data limited to 150000 rows` (o `exceeded the allowed volume`).

El lector [src/ipc/lector.py](../src/ipc/lector.py) rechaza los archivos truncados.

## Formato del archivo (referencia)

Power BI exporta en dos formatos y el lector entiende ambos:

| Formato | Cómo se ve | Límite |
|---|---|---|
| Largo (una fila por medida) | notas arriba; columnas `Medida` y `Medida_Dinamica` | 150.000 filas |
| Ancho (una columna por medida) | dos filas de encabezado; notas al final | ~9.400 filas |

- Dimensiones: Año, Mes, Nivel de ingresos, Nivel de canasta, División, Grupo, Clase, Subclase
  (como `01110100 - Arroz`), Cobertura Geografica.
- Números como texto con coma decimal (`155,06`). Hay celdas vacías: 10 ciudades y "Otras áreas
  urbanas" no tienen subclases publicadas, pero igual ocupan filas.
- 24 geografías: Nacional, 22 ciudades y Otras áreas urbanas (San Andrés y Quibdó van dentro de
  esta última).

## Dónde guardar los archivos

| En tu computador (no se sube a GitHub) | En Databricks |
|---|---|
| `data/historico/` | `/Volumes/ipc/bronze/raw/historico/` |
| `data/mensual/` | `/Volumes/ipc/bronze/raw/mensual/` |

**Subir**: **Catalog** → `ipc` → `bronze` → **Volumes** → `raw` → entra a la carpeta →
**Upload to this volume** → arrastra uno o varios archivos a la vez.

## Ponderadores (archivos de referencia)

En [referencia/](../referencia/) están los ponderadores oficiales del IPC base 2018 con los
códigos de la jerarquía:

- `ponderadores_subclase.csv`: 188 subclases × Pobres, Vulnerables, Clase Media, Altos, Total
- `ponderadores_division.csv`: 12 divisiones
- `ponderadores_ciudad.csv`: peso de 23 ciudades en el total nacional

Súbelos a una carpeta `referencia/` dentro del volumen `raw` (créala con **Create directory**).

## Cómo se consolidará (etapa 2)

1. **Bronze**: cada archivo tal cual, con el nombre del archivo y la fecha de carga.
2. **Silver**: unión de todos los archivos en una tabla con clave
   (fecha, nivel de ingreso, ciudad, nivel de canasta, código). Si una clave llega dos veces, gana
   el archivo cargado más reciente. Se agrega dic-2018 = 100 y se marca el dominio (oficial
   geográfico, oficial ingresos o consulta).
3. **Validaciones**: ningún mes faltante desde 2019, ningún archivo truncado y total nacional igual
   al anexo del DANE.
4. **Gold**: variaciones (mensual, año corrido, anual), contribuciones con los ponderadores,
   rankings y brechas.

## ✅ Checkpoint
Los 10 archivos históricos están en `/Volumes/ipc/bronze/raw/historico/` sin aviso de truncado.

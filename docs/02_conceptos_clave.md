# 02 · Conceptos clave (lo mínimo para empezar)

## Notebook
Documento con celdas de código (Python o SQL) y texto, como Jupyter. En este repo los notebooks están
guardados como archivos `.py` con marcas especiales (`# COMMAND ----------` separa celdas y
`# MAGIC %md` es una celda de texto). Databricks los abre como notebooks normales.

Dentro de un notebook de Databricks ya existen:
- `spark`: el motor para leer, transformar y escribir datos (tablas grandes).
- `dbutils`: utilidades (archivos, widgets/parámetros, secretos).
- `display(df)`: muestra una tabla interactiva con opción de gráfico.

## Unity Catalog: cómo se organizan los datos
Todo dato tiene un nombre de **tres niveles**: `catalogo.esquema.tabla`.

```
ipc                      ← catálogo (el proyecto)
├── bronze               ← esquema
│   ├── raw              ← volumen: carpeta para archivos (xlsx, csv)
│   └── ipc_crudo        ← tabla
├── silver
│   └── ipc              ← tabla limpia
└── gold
    ├── ipc_consulta
    └── resumen_mes
```

- **Tabla**: datos con columnas, se consultan con SQL. Se guardan en formato **Delta**
  (permite actualizar, borrar e incluso ver versiones anteriores: *time travel*).
- **Volumen** (*Volume*): carpeta para archivos sueltos. Su ruta es
  `/Volumes/ipc/bronze/raw/...`.

## Arquitectura medallion (bronze → silver → gold)
Una convención para ordenar el procesamiento:

| Capa | Contenido | En este proyecto |
|---|---|---|
| **Bronze** | Lo crudo, sin tocar | Los archivos exportados del DANE y una tabla con esas filas tal cual |
| **Silver** | Limpio y confiable | Fechas como fecha, números como números, nombres estandarizados, sin duplicados, una fila por mes × ciudad × ingreso × rubro |
| **Gold** | Listo para consumir | Tablas que alimentan directamente los tableros (variaciones, rankings, brechas) |

## Serverless
No administras servidores: cuando ejecutas una celda, Databricks asigna cómputo y lo apaga al
terminar. En Free Edition es la única opción y es justo lo que queremos.

## Job (Lakeflow Jobs)
Una secuencia de tareas (por ejemplo notebooks) que corre sola: con horario o cuando **llega un
archivo nuevo** a un volumen (*file arrival trigger*). Usaremos esto último: subes el archivo del mes
y el job procesa todo.

## Dashboard (AI/BI)
Tableros con gráficos, tablas y filtros construidos sobre consultas SQL. Se pueden compartir.

## Git folder
Una carpeta del workspace conectada a un repositorio de GitHub. Así el código vive en GitHub
y lo traes a Databricks con un clic (*pull*).

## ✅ Checkpoint
Sabes qué significa `ipc.silver.ipc` y la diferencia entre una tabla y un volumen.

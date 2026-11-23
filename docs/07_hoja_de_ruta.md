# 07 · Hoja de ruta

## Etapa 1 · Arranque ✅ (esta)
Repo, entorno local, cuenta Free Edition, catálogo, volumen y primer archivo explorado.

## Etapa 2 · Pipeline de datos
- ✅ `notebooks/10_bronze_ingesta`: carga los xlsx del volumen en `ipc.bronze.ipc_indices` con
  columnas de auditoría. Incremental (control en `ipc.bronze.archivos_cargados`).
- ✅ `notebooks/20_silver_ipc`: consolida en `ipc.silver.ipc_indices` (gana la carga más reciente),
  marca el `dominio` (geografico | ingresos | consulta), agrega dic-2018 = 100, carga los
  ponderadores y corre las validaciones.
- `notebooks/30_gold` (en SQL): tablas para los tableros:
  - `ipc_consulta`: serie con variación mensual, anual y año corrido, lista para filtrar.
  - `contribuciones`: aporte (p.p.) de cada división y subclase a la inflación nacional por
    nivel de ingreso.
  - `brechas`: nivel de ingreso vs. total, pobres vs. altos y ciudad vs. nacional, con su cambio
    frente al mes anterior y al mismo mes del año anterior.
  - Vistas del último mes: `resumen_kpi`, `resumen_ranking`, `resumen_brechas`.

## Etapa 3 · Orquestación
- ✅ Job `ipc_mensual` creado a mano en **Jobs & Pipelines** con tareas bronze → silver → gold
  (serverless, parámetro `catalogo` = `ipc` en cada tarea). Primera corrida manual: 2 min.
  La tarea de refresco del dashboard se agrega en la etapa 4.
- ✅ Disparador **file arrival** sobre `/Volumes/ipc/bronze/raw/mensual/` (sí está disponible en
  Free Edition): al subir el archivo del mes se ejecuta todo. Pendiente: confirmarlo con el archivo
  de nov-2026 (diciembre). Plan B: horario mensual, día 10.
- ✅ Notificación por correo al terminar o fallar.
- Nota: el job usa los notebooks de la Git folder del workspace → hacer **Pull** tras cada cambio
  en GitHub (o configurar la sección *Git* del job para leer directamente de `main`).

## Etapa 4 · Tableros (AI/BI Dashboards)
- **Consulta**: filtros de división de gasto, nivel de ingreso, ciudad, año y mes; línea de índice
  y variación anual, tabla detallada, mapa/barras por ciudad.
- **Resumen del último mes**: KPIs (inflación mensual, anual, año corrido), top 10 subclases que más
  subieron/bajaron, divisiones con mayor contribución, evolución de brechas por ingreso y ciudad.
- El **Resumen** está versionado en `dashboards/ipc_resumen_mes.lvdash.json` (páginas Resumen y
  Brechas): se abre desde la Git folder tras un Pull. Los cambios hechos en la interfaz se guardan
  en ese mismo archivo y se suben con Commit & Push.

## Etapa 5 · Mejoras opcionales
- Descarga automática del archivo mensual desde appindices: primero revisar en DevTools → Network
  si el reporte usa la llamada `querydata` de Power BI (replicable con `requests`); si no, Selenium.
  Corre fuera de Databricks (Mac con launchd o GitHub Actions) y sube el xlsx al volumen.
- Databricks App (Streamlit) para una consulta más personalizada.
- Genie (preguntas en lenguaje natural sobre las tablas gold).
- CI con GitHub Actions: `pytest` en cada push a `main`.
- (Avanzado) Databricks CLI y Asset Bundles para desplegar como código.

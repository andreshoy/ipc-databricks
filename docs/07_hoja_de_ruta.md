# 07 · Hoja de ruta

## Etapa 1 · Arranque ✅ (esta)
Repo, entorno local, cuenta Free Edition, catálogo, volumen y primer archivo explorado.

## Etapa 2 · Pipeline de datos
- `notebooks/10_bronze_ingesta`: lee todos los xlsx del volumen y los guarda en `ipc.bronze.ipc_crudo`
  con columnas de auditoría (archivo origen, fecha de carga). Procesa solo archivos nuevos.
- `notebooks/20_silver_ipc`: limpia y tipa (fecha = primer día del mes), estandariza nombres de
  ciudad/ingreso/rubro, separa jerarquía (división → grupo → clase → subclase) y hace `MERGE`
  (sin duplicados) en `ipc.silver.ipc`. Clave: fecha + ciudad + ingreso + nivel + código.
- `notebooks/30_gold_*`: tablas para tableros:
  - `ipc_consulta`: serie lista para filtrar por división, ingreso, ciudad, mes y año.
  - `resumen_mes`: último mes, ranking de mayores/menores variaciones (mensual y anual),
    contribuciones, y **brechas** (p. ej. inflación pobres vs. altos, ciudad vs. nacional) y su
    cambio frente al mes anterior y al mismo mes del año anterior.
- Calidad de datos: chequeos simples (meses faltantes, índices nulos, duplicados).

## Etapa 3 · Orquestación
- Job `ipc_mensual` definido en el bundle (`resources/ipc_job.yml`) con tareas
  bronze → silver → gold → refresco de dashboard.
- Disparador **file arrival** sobre `/Volumes/ipc/bronze/raw/mensual/`: al subir el archivo del mes
  se ejecuta todo. (Si el disparador no estuviera disponible en Free Edition, usar horario mensual,
  p. ej. día 10 de cada mes, ya que el DANE publica el IPC los primeros días del mes.)
- Notificación por correo al terminar o fallar.

## Etapa 4 · Tableros (AI/BI Dashboards)
- **Consulta**: filtros de división de gasto, nivel de ingreso, ciudad, año y mes; línea de índice
  y variación anual, tabla detallada, mapa/barras por ciudad.
- **Resumen del último mes**: KPIs (inflación mensual, anual, año corrido), top 10 subclases que más
  subieron/bajaron, divisiones con mayor contribución, evolución de brechas por ingreso y ciudad.
- Ambos versionados en el repo (`*.lvdash.json`) y desplegados con el bundle.

## Etapa 5 · Mejoras opcionales
- Databricks App (Streamlit) para una consulta más personalizada.
- Genie (preguntas en lenguaje natural sobre las tablas gold).
- CI con GitHub Actions: `pytest` + `databricks bundle validate/deploy` en cada push a `main`.

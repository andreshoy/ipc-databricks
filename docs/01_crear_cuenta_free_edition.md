# 01 · Crear tu cuenta de Databricks Free Edition

**Free Edition** es la versión gratuita y permanente de Databricks para aprender (reemplazó a la
antigua *Community Edition*). No pide tarjeta de crédito y no caduca.

## Pasos

1. Entra a <https://www.databricks.com/learn/free-edition> y haz clic en **Sign up**.
2. Regístrate con tu correo personal o con tu cuenta de Google/Microsoft.
   - Si te ofrece "Free trial" (prueba de 14 días con tu nube) o "Free Edition", elige **Free Edition**.
3. Confirma el correo. En un par de minutos tendrás tu **workspace** (tu espacio de trabajo).
4. Guarda la **URL del workspace** que aparece en el navegador. Se parece a
   `https://dbc-xxxxxxxx-xxxx.cloud.databricks.com`. La necesitarás en el paso 04.

## Tour rápido por la interfaz (menú de la izquierda)

| Menú | Qué es | Lo usaremos para |
|---|---|---|
| **Workspace** | Carpetas con notebooks y archivos | Clonar este repo (paso 03) |
| **Catalog** | Explorador de datos (Unity Catalog) | Ver tablas y el volumen de archivos |
| **Jobs & Pipelines** | Tareas programadas | Proceso mensual automático |
| **SQL Editor** | Escribir consultas SQL | Explorar datos |
| **Dashboards** | Tableros AI/BI | Tablero de consulta y resumen |
| **Compute** | Recursos de cómputo | En Free Edition todo es *serverless*: no hay que crear clusters |

## Límites de Free Edition que conviene conocer

- Solo cómputo **serverless** (se enciende solo, no configuras servidores).
- Un **SQL warehouse** de tamaño 2X-Small (suficiente para este proyecto).
- Máximo 5 tareas de jobs en paralelo.
- **Internet de salida restringido** a algunos dominios de confianza → por eso la descarga del DANE
  se hace fuera de Databricks.
- Hay una cuota de uso justo: si te pasas, el cómputo se apaga hasta el día siguiente.
  Con los volúmenes del IPC no deberías acercarte.

Referencia: <https://docs.databricks.com/aws/en/getting-started/free-edition-limitations>

## ✅ Checkpoint
Puedes entrar a tu workspace y ves el menú de la izquierda. Tienes anotada la URL del workspace.

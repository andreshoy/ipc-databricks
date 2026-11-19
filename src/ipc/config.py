"""Configuración central del proyecto IPC.

Todos los notebooks y scripts leen los nombres de catálogo, esquemas y volumen desde aquí,
así si algo cambia (por ejemplo, si tu cuenta no permite crear el catálogo ``ipc``) solo
se modifica en un lugar o con la variable de entorno ``IPC_CATALOG``.
"""

import os

# --- Fuente de datos ---------------------------------------------------------
# Consulta dinámica del IPC base 2018 (reporte Power BI embebido; exportación manual).
FUENTE_URL = "https://appindices.dane.gov.co/"
GUIA_USUARIO_URL = "https://appindices.dane.gov.co/resources/pdf/guia_de_usuario.pdf"
ANIO_INICIO = 2018

# --- Unity Catalog -----------------------------------------------------------
CATALOG = os.environ.get("IPC_CATALOG", "ipc")

SCHEMA_BRONZE = "bronze"  # datos crudos, tal como llegan
SCHEMA_SILVER = "silver"  # datos limpios y tipados
SCHEMA_GOLD = "gold"  # tablas listas para tableros

VOLUME_RAW = "raw"  # carpeta de archivos dentro de bronze

# Subcarpetas dentro del volumen
CARPETA_HISTORICO = "historico"  # exportaciones por tramos (carga inicial)
CARPETA_MENSUAL = "mensual"  # exportación de cada nuevo mes

# Dimensiones esperadas en la exportación de appindices
NIVELES_INGRESO = ["Total", "Ingresos Altos", "Clase Media", "Vulnerables", "Pobres"]
NIVELES_CANASTA = ["Total", "División", "Grupo", "Clase", "Subclase"]


def fq(schema: str, objeto: str) -> str:
    """Nombre completo de tres niveles: ``catalogo.esquema.objeto``."""
    return f"{CATALOG}.{schema}.{objeto}"


def volume_path(*partes: str) -> str:
    """Ruta POSIX al volumen de archivos crudos, p. ej. ``/Volumes/ipc/bronze/raw/mensual``."""
    base = f"/Volumes/{CATALOG}/{SCHEMA_BRONZE}/{VOLUME_RAW}"
    return "/".join([base, *partes]) if partes else base

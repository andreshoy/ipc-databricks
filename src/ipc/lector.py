"""Lectura de los archivos exportados desde appindices.dane.gov.co (Power BI).

Power BI exporta en dos formatos según cómo esté la tabla en pantalla (hoja "Export"):

**Ancho** (medidas como columnas):
- Fila "Medida": nombres de las medidas (Número Índice, Variación Mensual, ...).
- Fila de dimensiones: Año, Mes, Nivel de ingresos, Nivel de canasta, jerarquía
  División/Grupo/Clase/Subclase ("01110100 - Arroz"), Cobertura Geografica; luego una columna
  por medida. Las notas ("Filtros aplicados", avisos) van al final.
- Se corta en ~9.400 filas: "Exported data exceeded the allowed volume...".

**Largo** (una fila por medida):
- Notas al inicio, luego encabezado: las mismas dimensiones + "Medida" + "Medida_Dinamica".
- Se corta en 150.000 filas: "Exported data limited to 150000 rows...".

En ambos: números como texto con coma decimal ("155,06") y celdas vacías donde el DANE no
publica (p. ej. subclases de las ciudades pequeñas).
"""

from __future__ import annotations

import pandas as pd

AVISOS_TRUNCADO = ("Exported data exceeded the allowed volume", "Exported data limited to")

MESES = {
    "Ene": 1, "Feb": 2, "Mar": 3, "Abr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Ago": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dic": 12,
}  # fmt: skip

DIMENSIONES = {
    "Año": "anio",
    "Mes": "mes",
    "Nivel de ingresos": "nivel_ingresos",
    "Nivel de canasta": "nivel_canasta",
    "CIP_NOMBRE_v3 Jerarquía - División": "division",
    "CIP_NOMBRE_v3 Jerarquía - Grupo": "grupo",
    "CIP_NOMBRE_v3 Jerarquía - Clase": "clase",
    "CIP_NOMBRE_v3 Jerarquía - Subclase": "subclase",
    "Cobertura Geografica": "ciudad",
}

JERARQUIA = ["division", "grupo", "clase", "subclase"]


class ExportacionTruncada(ValueError):
    """El archivo trae el aviso de Power BI de que se omitieron datos."""


def nombre_medida(texto: str) -> str:
    """'Variación Año Corrido' -> 'variacion_ano_corrido'."""
    tabla = str.maketrans("áéíóúñÁÉÍÓÚÑ", "aeiounAEIOUN")
    return "_".join(texto.translate(tabla).lower().replace("ipc", "").split())


def leer_exportacion(ruta: str, permitir_truncado: bool = False) -> pd.DataFrame:
    """Lee un .xlsx de appindices (formato ancho o largo) y devuelve una tabla tipada.

    Una fila por (fecha, nivel_ingresos, nivel_canasta, ciudad, rubro). Columnas: anio, mes,
    fecha, nivel_ingresos, nivel_canasta, ciudad, {division,grupo,clase,subclase}_{codigo,nombre}
    y una columna float por medida exportada (numero_indice, variacion_mensual, ...).
    """
    crudo = pd.read_excel(ruta, header=None, dtype=str)
    col0 = crudo.iloc[:, 0].fillna("")

    truncado = any(col0.str.contains(a, regex=False).any() for a in AVISOS_TRUNCADO)
    if truncado and not permitir_truncado:
        raise ExportacionTruncada(
            f"{ruta}: Power BI omitió datos por exceder el límite. Exporta un rango más pequeño."
        )

    fila_dim = col0[col0 == "Año"].index[0]
    dimensiones = crudo.iloc[fila_dim]
    es_largo = "Medida_Dinamica" in set(dimensiones) and "Medida" in set(dimensiones)

    if es_largo:
        columnas = [DIMENSIONES.get(c, c) for c in dimensiones]
    else:
        medidas = crudo.iloc[fila_dim - 1]
        columnas = [
            DIMENSIONES.get(d, d) if d in DIMENSIONES else nombre_medida(str(m))
            for d, m in zip(dimensiones, medidas, strict=True)
        ]

    df = crudo.iloc[fila_dim + 1 :].copy()
    df.columns = columnas
    df = df[df["anio"].str.fullmatch(r"\d{4}", na=False)]
    claves = list(DIMENSIONES.values())

    if es_largo:
        df["Medida"] = df["Medida"].map(nombre_medida)
        # groupby con dropna=False conserva claves vacías (p. ej. subclase en filas de división)
        df = (
            df.groupby([*claves, "Medida"], dropna=False, sort=False)["Medida_Dinamica"]
            .first()
            .unstack("Medida")
        )
        df.columns.name = None
        df = df.reset_index()
        medidas_cols = [c for c in df.columns if c not in claves]
    else:
        medidas_cols = [c for c in df.columns if c not in claves]

    df = df.reset_index(drop=True)
    df["anio"] = df["anio"].astype(int)
    df["mes"] = df["mes"].map(MESES).astype(int)
    df["fecha"] = pd.to_datetime(dict(year=df["anio"], month=df["mes"], day=1))

    for nivel in JERARQUIA:
        partes = df[nivel].str.split(" - ", n=1, expand=True)
        df[f"{nivel}_codigo"] = partes[0].str.strip() if 0 in partes else None
        df[f"{nivel}_nombre"] = partes[1].str.strip() if 1 in partes else None
    df = df.drop(columns=JERARQUIA)

    for c in medidas_cols:
        df[c] = pd.to_numeric(df[c].str.replace(",", ".", regex=False), errors="coerce")

    # Filas sin ningún valor (ciudades/rubros que el DANE no publica) no aportan nada
    df = df.dropna(subset=medidas_cols, how="all").reset_index(drop=True)
    df.attrs["truncado"] = bool(truncado)
    return df

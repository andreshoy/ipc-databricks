"""Lectura de los archivos exportados desde appindices.dane.gov.co (Power BI).

Formato observado en las exportaciones .xlsx (hoja "Export"):

- Fila 1: nombres de las medidas (Número Índice, Variación Mensual, ...) desde la columna 10.
- Fila 2: nombres de las dimensiones (Año, Mes, Nivel de ingresos, Nivel de canasta, jerarquía
  División/Grupo/Clase/Subclase como "01110100 - Arroz", Cobertura Geografica).
- Datos: números como texto con coma decimal ("155,06"); celdas vacías cuando el DANE no publica.
- Pie: una fila vacía, "Filtros aplicados: ..." y, si se pasó del límite de exportación,
  "Exported data exceeded the allowed volume. Some data may have been omitted."
"""

from __future__ import annotations

import pandas as pd

AVISO_TRUNCADO = "Exported data exceeded the allowed volume"

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


def _nombre_medida(texto: str) -> str:
    """'Variación Año Corrido' -> 'variacion_ano_corrido'."""
    tabla = str.maketrans("áéíóúñÁÉÍÓÚÑ", "aeiounAEIOUN")
    return "_".join(texto.translate(tabla).lower().replace("ipc", "").split())


def leer_exportacion(ruta: str, permitir_truncado: bool = False) -> pd.DataFrame:
    """Lee un .xlsx de appindices y devuelve una tabla larga y tipada (una fila por registro).

    Columnas: anio, mes, fecha, nivel_ingresos, nivel_canasta, ciudad,
    {division,grupo,clase,subclase}_{codigo,nombre} y una columna float por medida.
    """
    crudo = pd.read_excel(ruta, header=None, dtype=str)

    pie = crudo.iloc[:, 0].fillna("")
    truncado = pie.str.contains(AVISO_TRUNCADO, regex=False).any()
    if truncado and not permitir_truncado:
        raise ExportacionTruncada(
            f"{ruta}: Power BI omitió datos por exceder el límite. Exporta un rango más pequeño."
        )

    medidas = crudo.iloc[0]
    dimensiones = crudo.iloc[1]
    columnas = [
        DIMENSIONES.get(dimensiones[i], dimensiones[i]) if i < 9 else _nombre_medida(medidas[i])
        for i in range(crudo.shape[1])
    ]
    df = crudo.iloc[2:].copy()
    df.columns = columnas
    df = df[df["anio"].str.fullmatch(r"\d{4}", na=False)].reset_index(drop=True)

    df["anio"] = df["anio"].astype(int)
    df["mes"] = df["mes"].map(MESES).astype(int)
    df["fecha"] = pd.to_datetime(dict(year=df["anio"], month=df["mes"], day=1))

    for nivel in JERARQUIA:
        partes = df[nivel].str.split(" - ", n=1, expand=True)
        df[f"{nivel}_codigo"] = partes[0].str.strip() if 0 in partes else None
        df[f"{nivel}_nombre"] = partes[1].str.strip() if 1 in partes else None
    df = df.drop(columns=JERARQUIA)

    columnas_medida = [c for c in columnas[9:]]
    for c in columnas_medida:
        df[c] = pd.to_numeric(df[c].str.replace(",", ".", regex=False), errors="coerce")

    df.attrs["truncado"] = bool(truncado)
    return df

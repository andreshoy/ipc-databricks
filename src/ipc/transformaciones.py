"""Transformaciones bronze -> silver (pandas puro: se prueban en local y corren en Databricks).

Bronze: una fila por registro de cada archivo, tal como viene, con columnas de auditoría.
Silver: una fila por serie y mes, sin duplicados, con dominio de difusión y base dic-2018 = 100.
"""

from __future__ import annotations

import pandas as pd

TOTAL = "Total Nivel de Ingresos"
BASE = pd.Timestamp("2018-12-01")

JERARQUIA = ["division", "grupo", "clase", "subclase"]
COLUMNAS_JERARQUIA = [f"{n}_{p}" for n in JERARQUIA for p in ("codigo", "nombre")]

COLUMNAS_BRONZE = [
    "fecha", "anio", "mes", "nivel_ingresos", "nivel_canasta", "ciudad",
    *COLUMNAS_JERARQUIA, "numero_indice", "archivo_origen", "cargado_en",
]  # fmt: skip

# Clave de negocio: identifica una serie (sin la fecha) y un dato (con la fecha)
CLAVE_SERIE = ["nivel_ingresos", "ciudad", "nivel_canasta", "codigo"]
CLAVE = ["fecha", *CLAVE_SERIE]

NIVEL_A_PREFIJO = {
    "Division": "division",
    "Grupo": "grupo",
    "Clase": "clase",
    "Subclase": "subclase",
}


def preparar_bronze(df: pd.DataFrame, archivo: str, cargado_en: pd.Timestamp) -> pd.DataFrame:
    """Deja la salida del lector con columnas fijas + auditoría (archivo y fecha de carga)."""
    out = df.copy()
    for c in COLUMNAS_JERARQUIA:
        if c not in out:
            out[c] = None
    out["archivo_origen"] = archivo
    out["cargado_en"] = cargado_en
    out = out[COLUMNAS_BRONZE]
    out = out[out["numero_indice"].notna()]
    texto = [
        c
        for c in COLUMNAS_BRONZE
        if c not in ("fecha", "anio", "mes", "numero_indice", "cargado_en")
    ]
    out[texto] = out[texto].astype(object).where(out[texto].notna(), None)
    return out.reset_index(drop=True)


def dominio(nivel_ingresos: pd.Series, ciudad: pd.Series) -> pd.Series:
    """Dominio de difusión del DANE.

    - geografico: Total de ingresos, nacional y ciudades (oficial)
    - ingresos: nacional por nivel de ingreso (oficial)
    - consulta: ciudad x nivel de ingreso (aparece en appindices pero no es dominio oficial)
    """
    return pd.Series(
        [
            "geografico" if ni == TOTAL else ("ingresos" if c == "NACIONAL" else "consulta")
            for ni, c in zip(nivel_ingresos, ciudad, strict=True)
        ],
        index=nivel_ingresos.index,
    )


def construir_silver(bronze: pd.DataFrame) -> pd.DataFrame:
    """Une todos los archivos, quita duplicados (gana la carga más reciente) y agrega la base."""
    df = bronze.copy()
    df["fecha"] = pd.to_datetime(df["fecha"])

    # Código y nombre del rubro según su nivel (Total = 00000000)
    df["codigo"] = "00000000"
    df["nombre"] = "Total"
    for nivel, prefijo in NIVEL_A_PREFIJO.items():
        m = df["nivel_canasta"] == nivel
        df.loc[m, "codigo"] = df.loc[m, f"{prefijo}_codigo"]
        df.loc[m, "nombre"] = df.loc[m, f"{prefijo}_nombre"]

    df = (
        df.sort_values("cargado_en")
        .drop_duplicates(CLAVE, keep="last")
        .sort_values(CLAVE)
        .reset_index(drop=True)
    )
    df["dominio"] = dominio(df["nivel_ingresos"], df["ciudad"])
    df = agregar_base(df)
    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month

    columnas = [
        "fecha", "anio", "mes", "dominio", *CLAVE_SERIE, "nombre", *COLUMNAS_JERARQUIA,
        "numero_indice", "archivo_origen", "cargado_en",
    ]  # fmt: skip
    return df[columnas].sort_values(CLAVE).reset_index(drop=True)


def agregar_base(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega dic-2018 = 100 a cada serie que empieza en ene-2019 (la base del IPC 2018)."""
    inicio = df.groupby(CLAVE_SERIE, dropna=False)["fecha"].transform("min")
    primeras = df[(df["fecha"] == inicio) & (df["fecha"] == pd.Timestamp("2019-01-01"))]
    base = primeras.copy()
    base["fecha"] = BASE
    base["numero_indice"] = 100.0
    base["archivo_origen"] = "base_dic2018"
    return pd.concat([df[df["fecha"] != BASE], base], ignore_index=True)


def validar(silver: pd.DataFrame, oficiales: dict | None = None) -> pd.DataFrame:
    """Chequeos de calidad. Devuelve una fila por chequeo con su resultado."""
    checks = []

    def check(nombre, ok, detalle):
        checks.append({"chequeo": nombre, "resultado": "✅" if ok else "❌", "detalle": detalle})

    dups = int(silver.duplicated(CLAVE).sum())
    check("Sin duplicados en la clave", dups == 0, f"{dups} duplicados")

    # Meses faltantes en las series nacionales Total (una por nivel de ingreso)
    tot = silver[(silver.ciudad == "NACIONAL") & (silver.nivel_canasta == "Total")]
    esperado = pd.date_range(BASE, silver["fecha"].max(), freq="MS")
    faltan = {ni: len(esperado.difference(g["fecha"])) for ni, g in tot.groupby("nivel_ingresos")}
    check(
        "Series nacionales completas desde dic-2018",
        sum(faltan.values()) == 0 and len(faltan) == 5,
        f"meses faltantes por nivel de ingreso: {faltan}",
    )

    geos = silver[silver.dominio == "geografico"].groupby("fecha")["ciudad"].nunique()
    check(
        "24 geografías en cada mes (Total)",
        (geos == 24).all(),
        f"mín {geos.min()}, máx {geos.max()}",
    )

    if oficiales:
        t = tot[tot.nivel_ingresos == TOTAL]
        difs = [
            abs(r.numero_indice - oficiales[(r.fecha.year, r.fecha.month)])
            for r in t.itertuples()
            if (r.fecha.year, r.fecha.month) in oficiales
        ]
        check(
            "Total nacional = anexo DANE",
            bool(difs) and max(difs) < 0.005,
            f"{len(difs)} meses comparados, dif. máx {max(difs):.3f}" if difs else "sin datos",
        )

    check(
        "Índices positivos",
        bool((silver.numero_indice > 0).all()),
        f"mín {silver.numero_indice.min():.2f}",
    )
    return pd.DataFrame(checks)

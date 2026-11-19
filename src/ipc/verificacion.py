"""Verificación de los archivos exportados de appindices (sirve en local y en Databricks)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ipc.lector import leer_exportacion

TOTAL = "Total Nivel de Ingresos"


def indices_oficiales(ruta_anexo: str | Path) -> dict[tuple[int, int], float]:
    """Lee anex-IPC-Indices-*.xlsx del DANE -> {(año, mes): índice total nacional}."""
    d = pd.read_excel(ruta_anexo, header=None)
    fila = d.index[d[0] == "Mes"][0]
    oficiales = {}
    for col, anio in d.iloc[fila].items():
        try:
            anio = int(float(anio))
        except (TypeError, ValueError):
            continue
        for mes in range(1, 13):
            valor = d.iloc[fila + mes, col]
            if pd.notna(valor):
                oficiales[(anio, mes)] = float(valor)
    return oficiales


def resumen_archivo(ruta: str | Path, oficiales: dict | None = None) -> dict:
    """Una fila de resumen por archivo: completo/truncado, cobertura y cuadre con el DANE."""
    ruta = Path(ruta)
    fila = {"carpeta": ruta.parent.name, "archivo": ruta.name}
    try:
        df = leer_exportacion(ruta, permitir_truncado=True)
    except Exception as e:  # noqa: BLE001 - queremos reportar cualquier problema de lectura
        return {**fila, "estado": f"❌ error: {e}"}

    medidas = [c for c in df.columns if c.startswith(("numero", "variacion", "contribucion"))]
    total_nac = df[
        (df.ciudad == "NACIONAL") & (df.nivel_canasta == "Total") & (df.nivel_ingresos == TOTAL)
    ]
    dif = None
    if oficiales:
        difs = [
            abs(r.numero_indice - oficiales[(r.anio, r.mes)])
            for r in total_nac.itertuples()
            if (r.anio, r.mes) in oficiales
        ]
        dif = round(max(difs), 3) if difs else None

    return {
        **fila,
        "estado": "❌ TRUNCADO" if df.attrs["truncado"] else "✅ completo",
        "registros": len(df),
        "desde": df.fecha.min().strftime("%Y-%m"),
        "hasta": df.fecha.max().strftime("%Y-%m"),
        "meses": df.fecha.nunique(),
        "ingresos": df.nivel_ingresos.nunique(),
        "geografias": df.ciudad.nunique(),
        "niveles_canasta": df.nivel_canasta.nunique(),
        "solo_numero_indice": medidas == ["numero_indice"],
        "dif_max_vs_anexo": dif,
    }


def verificar_carpetas(base: str | Path, carpetas=("historico", "mensual")) -> pd.DataFrame:
    """Resume todos los .xlsx de las carpetas indicadas dentro de ``base``."""
    base = Path(base)
    anexos = sorted((base / "referencia").glob("anex-IPC-Indices-*.xlsx"))
    oficiales = indices_oficiales(anexos[-1]) if anexos else None
    filas = [
        resumen_archivo(ruta, oficiales)
        for carpeta in carpetas
        for ruta in sorted((base / carpeta).glob("*.xlsx"))
    ]
    return pd.DataFrame(filas)


def cobertura(base: str | Path, carpetas=("historico", "mensual")) -> pd.DataFrame:
    """Meses con datos por año, para el dominio ciudades (Total) y para cada nivel de ingreso."""
    base = Path(base)
    datos = pd.concat(
        [
            leer_exportacion(r, permitir_truncado=True)
            for c in carpetas
            for r in sorted((base / c).glob("*.xlsx"))
        ]
    )
    nacional = datos[datos.ciudad == "NACIONAL"]
    tabla = nacional.groupby(["nivel_ingresos", "anio"]).mes.nunique().unstack(fill_value=0)
    ciudades = datos[datos.nivel_ingresos == TOTAL].groupby("anio").ciudad.nunique()
    tabla.loc["(ciudades con dato, Total)"] = ciudades
    return tabla

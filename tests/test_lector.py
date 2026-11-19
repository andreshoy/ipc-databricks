"""Pruebas del lector con los archivos de ejemplo locales (data/ no se sube a GitHub)."""

from pathlib import Path

import pytest

from ipc.lector import ExportacionTruncada, leer_exportacion

DATA = Path(__file__).parent.parent / "data"
ANCHO = DATA / "ejemplos" / "data.xlsx"  # formato ancho, oct-2026, completo
LARGO = DATA / "historico" / "ipc_2026.xlsx"  # formato largo, truncado en 150.000 filas


@pytest.mark.skipif(not ANCHO.exists(), reason="sin archivo de ejemplo local")
def test_lee_formato_ancho():
    df = leer_exportacion(ANCHO)
    assert not df.attrs["truncado"]
    fila = df[(df.ciudad == "NACIONAL") & (df.subclase_codigo == "01110100")].iloc[0]
    assert fila["subclase_nombre"] == "Arroz"
    assert fila["numero_indice"] == pytest.approx(155.06)
    assert str(fila["fecha"].date()) == "2026-10-01"
    assert (df.groupby(["ciudad", "subclase_codigo"]).size() == 1).all()


@pytest.mark.skipif(not LARGO.exists(), reason="sin archivo largo local")
def test_lee_formato_largo_y_detecta_truncado():
    with pytest.raises(ExportacionTruncada):
        leer_exportacion(LARGO)
    df = leer_exportacion(LARGO, permitir_truncado=True)
    assert df.attrs["truncado"]
    fila = df[(df.ciudad == "NACIONAL") & (df.subclase_codigo == "01110100") & (df.mes == 1)]
    assert fila["numero_indice"].iloc[0] == pytest.approx(153.36)
    assert fila["variacion_mensual"].iloc[0] == pytest.approx(-0.59)

"""Pruebas del lector con los archivos de ejemplo locales (data/ no se sube a GitHub)."""

from pathlib import Path

import pytest

from ipc.lector import ExportacionTruncada, leer_exportacion

DATA = Path(__file__).parent.parent / "data"
EJEMPLO = DATA / "ejemplos" / "data.xlsx"
TRUNCADO = DATA / "historico" / "ipc_2026.xlsx"


@pytest.mark.skipif(not EJEMPLO.exists(), reason="sin archivo de ejemplo local")
def test_lee_ejemplo_mensual():
    df = leer_exportacion(EJEMPLO)
    assert not df.attrs["truncado"]
    assert len(df) > 2000
    fila = df.iloc[0]
    assert fila["subclase_codigo"] == "01110100"
    assert fila["subclase_nombre"] == "Arroz"
    assert fila["numero_indice"] == pytest.approx(155.06)
    assert str(fila["fecha"].date()) == "2026-10-01"
    assert "variacion_mensual" in df.columns


@pytest.mark.skipif(not TRUNCADO.exists(), reason="sin archivo truncado local")
def test_detecta_truncado():
    with pytest.raises(ExportacionTruncada):
        leer_exportacion(TRUNCADO)
    assert leer_exportacion(TRUNCADO, permitir_truncado=True).attrs["truncado"]

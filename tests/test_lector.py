"""Pruebas del lector: archivos locales reales (data/, no se sube a GitHub) y uno sintético."""

from pathlib import Path

import pandas as pd
import pytest

from ipc.lector import ExportacionTruncada, leer_exportacion

DATA = Path(__file__).parent.parent / "data"
MENSUAL = DATA / "mensual" / "ipc_2026_10.xlsx"
CIUDADES = DATA / "historico" / "ipc_ciudades_2019.xlsx"


@pytest.mark.skipif(not MENSUAL.exists(), reason="sin archivo mensual local")
def test_lee_mensual():
    df = leer_exportacion(MENSUAL)
    assert not df.attrs["truncado"]
    fila = df[
        (df.ciudad == "NACIONAL")
        & (df.nivel_ingresos == "Total Nivel de Ingresos")
        & (df.subclase_codigo == "01110100")
    ].iloc[0]
    assert fila["subclase_nombre"] == "Arroz"
    assert fila["numero_indice"] == pytest.approx(155.06)
    assert str(fila["fecha"].date()) == "2026-10-01"


@pytest.mark.skipif(not CIUDADES.exists(), reason="sin archivo histórico local")
def test_lee_historico_con_niveles_agregados():
    df = leer_exportacion(CIUDADES)
    total = df[(df.ciudad == "NACIONAL") & (df.nivel_canasta == "Total")]
    assert total.set_index("mes").numero_indice[12] == pytest.approx(103.80)
    assert set(df.nivel_canasta) == {"Total", "Division", "Grupo", "Clase", "Subclase"}


def _exportacion_sintetica(ruta: Path, truncada: bool):
    notas = [["Filtros aplicados: TIE_ANO es 2026"]]
    if truncada:
        notas.append(["Exported data limited to 150000 rows. Some data may have been omitted."])
    encabezado = [
        "Año", "Mes", "Nivel de ingresos", "Nivel de canasta",
        "CIP_NOMBRE_v3 Jerarquía - División", "CIP_NOMBRE_v3 Jerarquía - Grupo",
        "CIP_NOMBRE_v3 Jerarquía - Clase", "CIP_NOMBRE_v3 Jerarquía - Subclase",
        "Cobertura Geografica", "Medida", "Medida_Dinamica",
    ]  # fmt: skip
    datos = [
        ["2026", "Oct", "Pobres", "Total", None, None, None, None, "NACIONAL",
         "Número Índice", "164,92"],
        ["2026", "Oct", "Pobres", "Subclase", "01000000 - Alimentos", "01100000 - Alimentos",
         "01110000 - Pan Y Cereales", "01110100 - Arroz", "NACIONAL", "Número Índice", "155,20"],
    ]  # fmt: skip
    filas = [r + [None] * (len(encabezado) - len(r)) for r in notas] + [encabezado] + datos
    pd.DataFrame(filas).to_excel(ruta, header=False, index=False)


def test_sintetico_formato_largo(tmp_path):
    ruta = tmp_path / "ok.xlsx"
    _exportacion_sintetica(ruta, truncada=False)
    df = leer_exportacion(ruta)
    assert len(df) == 2
    assert df.loc[df.nivel_canasta == "Total", "numero_indice"].item() == pytest.approx(164.92)
    assert df.loc[df.nivel_canasta == "Subclase", "subclase_nombre"].item() == "Arroz"


def test_sintetico_detecta_truncado(tmp_path):
    ruta = tmp_path / "truncado.xlsx"
    _exportacion_sintetica(ruta, truncada=True)
    with pytest.raises(ExportacionTruncada):
        leer_exportacion(ruta)
    assert leer_exportacion(ruta, permitir_truncado=True).attrs["truncado"]

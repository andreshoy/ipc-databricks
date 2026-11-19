import pandas as pd

from ipc.transformaciones import COLUMNAS_BRONZE, construir_silver, validar


def _fila(fecha, ingreso, ciudad, nivel, codigo, indice, archivo, cargado):
    f = dict.fromkeys(COLUMNAS_BRONZE)
    f.update(
        fecha=pd.Timestamp(fecha),
        nivel_ingresos=ingreso,
        ciudad=ciudad,
        nivel_canasta=nivel,
        numero_indice=indice,
        archivo_origen=archivo,
        cargado_en=pd.Timestamp(cargado),
    )
    if nivel == "Subclase":
        f.update(subclase_codigo=codigo, subclase_nombre="Arroz", division_codigo="01000000")
    return f


def test_silver_dedup_dominio_y_base():
    T = "Total Nivel de Ingresos"
    bronze = pd.DataFrame(
        [
            _fila("2019-01-01", T, "NACIONAL", "Total", None, 100.60, "a.xlsx", "2026-01-01"),
            # mismo dato en otro archivo cargado después: debe ganar este
            _fila("2019-01-01", T, "NACIONAL", "Total", None, 100.61, "b.xlsx", "2026-02-01"),
            _fila(
                "2019-01-01", "Pobres", "NACIONAL", "Total", None, 100.63, "a.xlsx", "2026-01-01"
            ),
            _fila(
                "2019-01-01", "Pobres", "CALI", "Subclase", "01110100", 99.0, "c.xlsx", "2026-01-01"
            ),
        ]
    )
    s = construir_silver(bronze)

    tot = s[(s.nivel_ingresos == T) & (s.fecha == "2019-01-01")]
    assert tot.numero_indice.item() == 100.61 and tot.archivo_origen.item() == "b.xlsx"

    dom = s.drop_duplicates(["nivel_ingresos", "ciudad"]).set_index(["nivel_ingresos", "ciudad"])
    assert dom.loc[(T, "NACIONAL"), "dominio"] == "geografico"
    assert dom.loc[("Pobres", "NACIONAL"), "dominio"] == "ingresos"
    assert dom.loc[("Pobres", "CALI"), "dominio"] == "consulta"

    base = s[s.fecha == "2018-12-01"]
    assert len(base) == 3 and (base.numero_indice == 100).all()
    assert s[s.nivel_canasta == "Subclase"].codigo.iloc[0] == "01110100"

    checks = validar(s).set_index("chequeo")
    assert checks.loc["Sin duplicados en la clave", "resultado"] == "✅"

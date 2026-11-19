"""Prueba la verificación con la carpeta data/ local (simula /Volumes/ipc/bronze/raw)."""

from pathlib import Path

import pytest

from ipc.verificacion import verificar_carpetas

DATA = Path(__file__).parent.parent / "data"


@pytest.mark.skipif(not (DATA / "historico").exists(), reason="sin datos locales")
def test_verificar_carpetas_local():
    r = verificar_carpetas(DATA)
    assert len(r) > 0
    assert r.estado.str.startswith("✅").all()
    assert r.solo_numero_indice.all()
    assert (r.dif_max_vs_anexo.fillna(0) == 0).all()

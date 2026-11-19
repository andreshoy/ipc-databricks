from ipc import config


def test_nombres_completos():
    assert config.fq("silver", "ipc") == f"{config.CATALOG}.silver.ipc"


def test_rutas_volumen():
    assert config.volume_path() == f"/Volumes/{config.CATALOG}/bronze/raw"
    assert config.volume_path("mensual").endswith("/raw/mensual")


def test_dependencias_instaladas():
    import databricks.sdk  # noqa: F401
    import openpyxl  # noqa: F401
    import pandas  # noqa: F401

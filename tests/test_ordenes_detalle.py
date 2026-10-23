# Historia: H-01
"""
Prueba de la rebanada vertical de la sesion 7: GET /ordenes/{id_ot}.
Usa la base de datos con los datos simulados del proyecto (data/seed.py),
sin crear tablas nuevas ni modificar datos.
"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import crear_db_temporal, eliminar_db
from app.main import app
from app.modules.ordenes.repositorio import RepositorioOT, obtener_repositorio_ot


@pytest.fixture
def cliente():
    """Cliente de pruebas apuntando a una copia de la base con los datos simulados."""
    ruta = crear_db_temporal(poblar=True)
    app.dependency_overrides[obtener_repositorio_ot] = lambda: RepositorioOT(ruta_db=ruta)
    yield TestClient(app)
    app.dependency_overrides.clear()
    eliminar_db(ruta)


def test_ot_existente_responde_200_con_datos_reales(cliente):
    respuesta = cliente.get("/ordenes/1")
    assert respuesta.status_code == 200
    assert "Mantenimiento preventivo 45k" in respuesta.text
    assert respuesta.json()["placa"] == "ABC-123"


def test_ot_inexistente_responde_404(cliente):
    respuesta = cliente.get("/ordenes/no-existe-zz")
    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Orden de trabajo no encontrada"


@pytest.mark.parametrize("valor", ["9999", "-1", "'", "%20", "1" * 500])
def test_entradas_inesperadas_responden_404(cliente, valor):
    """Reto 2 de la guia S7: entradas raras nunca deben provocar un error 500."""
    respuesta = cliente.get(f"/ordenes/{valor}")
    assert respuesta.status_code == 404

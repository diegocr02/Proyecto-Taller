# Historia: H-01
"""
Pruebas para el Modulo de Ordenes de Trabajo (OT).
Incluye pruebas de propiedad PBT con Hypothesis segun tasks.md y design.md.
"""

import sqlite3
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, strategies as st

from tests.conftest import crear_db_temporal, eliminar_db
from app.main import app
from app.modules.ordenes.repositorio import RepositorioOT, obtener_repositorio_ot
from app.modules.ordenes.schemas import OTCrear


@pytest.fixture
def ruta_db():
    """Base de datos temporal con el esquema del proyecto."""
    ruta = crear_db_temporal()
    yield ruta
    eliminar_db(ruta)


@pytest.fixture
def repo_temporal(ruta_db):
    """Repositorio de OT apuntando a la base temporal."""
    return RepositorioOT(ruta_db=ruta_db)


@pytest.fixture
def cliente_api(repo_temporal):
    """Cliente de pruebas para FastAPI con el repositorio de OT sobre la base temporal."""
    app.dependency_overrides[obtener_repositorio_ot] = lambda: repo_temporal
    yield TestClient(app)
    app.dependency_overrides.clear()


def contar_ot(ruta: str) -> int:
    with sqlite3.connect(ruta) as conexion:
        return conexion.execute("SELECT COUNT(*) FROM ordenes_trabajo;").fetchone()[0]


# Estrategia de generacion de datos validos para OTCrear
anio_actual = datetime.now().year
estrategia_texto_corto = st.text(
    alphabet=st.characters(categories=["L", "N", "Zs"]), min_size=1, max_size=40
).map(lambda s: s.strip() or "Valido")
estrategia_ot = st.builds(
    OTCrear,
    nombre=estrategia_texto_corto,
    dni=st.integers(min_value=10000000, max_value=99999999).map(str),
    placa=st.from_regex(r"[A-Z]{3}-[0-9]{3}", fullmatch=True),
    marca=estrategia_texto_corto,
    modelo=estrategia_texto_corto,
    anio=st.integers(min_value=1900, max_value=anio_actual),
    kilometraje=st.integers(min_value=0, max_value=999999),
    motivo=st.text(alphabet=st.characters(categories=["L", "N", "Zs"]), min_size=5, max_size=200).map(
        lambda s: s.strip() or "Mantenimiento general"
    ),
    tecnico=st.sampled_from(["Luis Pachas", "Luis Luna", "Miguel Torres"]),
    observaciones=st.none() | estrategia_texto_corto,
)

CAMPOS_BASE = {
    "nombre": "Cliente Simulado",
    "dni": "87654321",
    "placa": "ABC-123",
    "marca": "Toyota",
    "modelo": "Corolla",
    "anio": 2021,
    "kilometraje": 25000,
    "motivo": "Fallo electrico",
    "tecnico": "Luis Luna",
}


# Feature: asistente-taller-jorge-motors, Propiedad 1: Unicidad de identificadores de OT
# Valida: Requisito 1.2
@given(ordenes=st.lists(estrategia_ot, min_size=1, max_size=20))
def test_propiedad_1_unicidad_de_identificadores(repo_temporal, ordenes):
    """Para cualquier conjunto de N OT creadas, todos sus identificadores son distintos."""
    ids = [repo_temporal.crear_ot(datos)["id_ot"] for datos in ordenes]
    assert len(set(ids)) == len(ids)


# Feature: asistente-taller-jorge-motors, Propiedad 2: Round-trip de campos obligatorios de OT
# Valida: Requisito 1.3
@given(datos=estrategia_ot)
def test_propiedad_2_round_trip_campos_obligatorios(repo_temporal, datos):
    """Recuperar una OT creada con datos validos retorna exactamente los mismos valores."""
    creada = repo_temporal.crear_ot(datos)
    recuperada = repo_temporal.obtener_ot_por_id(creada["id_ot"])

    assert recuperada is not None
    assert recuperada.id == creada["id_ot"]
    for campo in ("nombre", "dni", "placa", "marca", "modelo", "anio", "kilometraje", "motivo", "tecnico"):
        assert getattr(recuperada, campo) == getattr(datos, campo), campo
    assert recuperada.estado == "abierta"
    assert recuperada.fecha_hora == creada["fecha_hora"]
    datetime.fromisoformat(recuperada.fecha_hora)


# Feature: asistente-taller-jorge-motors, Propiedad 3: Rechazo de OT con campos obligatorios faltantes
# Valida: Requisito 1.4
@given(omitidos=st.sets(st.sampled_from(sorted(CAMPOS_BASE)), min_size=1))
def test_propiedad_3_rechazo_campos_faltantes(cliente_api, ruta_db, omitidos):
    """Omitir cualquier subconjunto de campos obligatorios retorna 422, indica el campo y no crea la OT."""
    antes = contar_ot(ruta_db)
    datos = {k: v for k, v in CAMPOS_BASE.items() if k not in omitidos}

    respuesta = cliente_api.post("/ordenes", json=datos)

    assert respuesta.status_code == 422
    assert set(respuesta.json()["campos"]) == omitidos
    assert contar_ot(ruta_db) == antes


def test_creacion_ot_exitosa_via_endpoint(cliente_api, ruta_db):
    """Verifica que POST /ordenes retorna 201 con id_ot y mensaje."""
    respuesta = cliente_api.post("/ordenes", json={**CAMPOS_BASE, "observaciones": "Revision rapida"})
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["id_ot"] > 0
    assert cuerpo["mensaje"] == "OT creada exitosamente"
    assert contar_ot(ruta_db) == 1


@pytest.mark.parametrize(
    "campo,valor",
    [("dni", "1234567A"), ("anio", 1899), ("anio", anio_actual + 1), ("kilometraje", 1000000), ("placa", "A" * 11)],
)
def test_rechazo_valores_fuera_de_rango(cliente_api, campo, valor):
    """Valores fuera de rango retornan 422 indicando el campo."""
    respuesta = cliente_api.post("/ordenes", json={**CAMPOS_BASE, campo: valor})
    assert respuesta.status_code == 422
    assert respuesta.json()["campos"] == [campo]


def test_error_de_base_de_datos_retorna_503():
    """Si la escritura falla, se responde 503 sin exponer el detalle tecnico."""
    app.dependency_overrides[obtener_repositorio_ot] = lambda: RepositorioOT(ruta_db="Z:/no/existe/taller.db")
    try:
        respuesta = TestClient(app).post("/ordenes", json=CAMPOS_BASE)
    finally:
        app.dependency_overrides.clear()
    assert respuesta.status_code == 503

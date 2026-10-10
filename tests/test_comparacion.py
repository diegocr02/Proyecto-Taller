# Historia: H-05
"""
Pruebas del Modulo Comparacion (Requisito 5): propiedades 12 y 13.
"""

import sqlite3

import pytest
from hypothesis import given, strategies as st

from tests.conftest import McpEspia, crear_db_temporal, eliminar_db, insertar_repuestos
from app.modules.comparacion.repositorio import RepositorioComparacion, obtener_repositorio_comparacion

CAMPOS_RESULTADO = {"nombre", "codigo", "sistema", "conteo", "diferencia", "descuadre"}


@pytest.fixture
def ruta_db():
    ruta = crear_db_temporal()
    yield ruta
    eliminar_db(ruta)


def crear_cliente(cliente_con_mcp, ruta):
    return cliente_con_mcp(
        McpEspia(ruta_db=ruta),
        overrides={obtener_repositorio_comparacion: RepositorioComparacion(ruta_db=ruta)},
    )


estrategia_pares = st.lists(
    st.tuples(st.integers(min_value=0, max_value=10_000), st.integers(min_value=0, max_value=10_000)),
    min_size=1,
    max_size=10,
)


# Feature: asistente-taller-jorge-motors, Propiedad 12: Corrección del cálculo de diferencias en comparación de conteo físico
# Valida: Requisitos 5.1, 5.2
# Feature: asistente-taller-jorge-motors, Propiedad 13: Clasificación correcta del indicador de descuadre
# Valida: Requisito 5.3
@given(pares=estrategia_pares)
def test_propiedades_12_y_13_diferencia_y_descuadre(cliente_con_mcp, pares):
    """diferencia = conteo_fisico - sistema con signo; descuadre si y solo si diferencia != 0."""
    ruta = crear_db_temporal()
    try:
        inventario = [(f"REP-{i:03d}", f"Repuesto {i}", "unidad", 0, sistema) for i, (sistema, _) in enumerate(pares)]
        insertar_repuestos(ruta, inventario)
        items = [{"codigo": f"REP-{i:03d}", "conteo_fisico": conteo} for i, (_, conteo) in enumerate(pares)]

        respuesta = crear_cliente(cliente_con_mcp, ruta).post("/comparacion", json={"items": items})

        assert respuesta.status_code == 200
        resultados = respuesta.json()["resultados"]
        assert len(resultados) == len(pares)
        for fila, (sistema, conteo) in zip(resultados, pares):
            assert set(fila) == CAMPOS_RESULTADO
            assert fila["sistema"] == sistema
            assert fila["conteo"] == conteo
            assert fila["diferencia"] == conteo - sistema
            assert fila["descuadre"] is (conteo != sistema)
    finally:
        eliminar_db(ruta)


def test_comparacion_sin_items(cliente_con_mcp, ruta_db):
    mcp = McpEspia(ruta_db=ruta_db)
    respuesta = cliente_con_mcp(mcp).post("/comparacion", json={"items": []})
    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "Debe ingresar al menos un repuesto con su conteo físico"
    assert mcp.llamadas == 0


def test_comparacion_repuesto_inexistente_se_excluye(cliente_con_mcp, ruta_db):
    insertar_repuestos(ruta_db, [("REP-001", "Filtro", "unidad", 2, 5)])
    respuesta = crear_cliente(cliente_con_mcp, ruta_db).post(
        "/comparacion",
        json={"items": [{"codigo": "REP-001", "conteo_fisico": 3}, {"codigo": "NO-EXISTE", "conteo_fisico": 1}]},
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert [r["codigo"] for r in cuerpo["resultados"]] == ["REP-001"]
    assert cuerpo["no_encontrados"] == ["NO-EXISTE"]
    assert "NO-EXISTE" in cuerpo["mensaje"]


def test_comparacion_se_persiste(cliente_con_mcp, ruta_db):
    insertar_repuestos(ruta_db, [("REP-001", "Filtro", "unidad", 2, 5)])
    crear_cliente(cliente_con_mcp, ruta_db).post(
        "/comparacion", json={"items": [{"codigo": "REP-001", "conteo_fisico": 3}]}
    )
    with sqlite3.connect(ruta_db) as conexion:
        fila = conexion.execute("SELECT codigo, sistema, conteo, diferencia, descuadre FROM comparaciones_conteo;").fetchone()
    assert fila == ("REP-001", 5, 3, -2, 1)


def test_comparacion_mcp_no_disponible(cliente_con_mcp):
    respuesta = cliente_con_mcp(McpEspia(caido=True)).post(
        "/comparacion", json={"items": [{"codigo": "REP-001", "conteo_fisico": 1}]}
    )
    assert respuesta.status_code == 503
    assert respuesta.json()["detail"] == "El servicio de inventario no está disponible en este momento"

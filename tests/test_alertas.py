# Historia: H-04
"""
Pruebas del Modulo Alertas (Requisito 4): propiedad 11.
"""

from hypothesis import given, strategies as st

from tests.conftest import McpEspia, crear_db_temporal, eliminar_db, insertar_repuestos

estrategia_inventario = st.lists(
    st.tuples(st.integers(min_value=0, max_value=30), st.integers(min_value=0, max_value=30)),
    max_size=25,
).map(
    lambda filas: [
        (f"REP-{i:03d}", f"Repuesto simulado {i}", "unidad", minimo, cantidad)
        for i, (minimo, cantidad) in enumerate(filas, start=1)
    ]
)


# Feature: asistente-taller-jorge-motors, Propiedad 11: Corrección del filtrado de alertas de stock mínimo
# Valida: Requisitos 4.1, 4.2
@given(inventario=estrategia_inventario)
def test_propiedad_11_filtrado_de_alertas(cliente_con_mcp, inventario):
    """La lista contiene exactamente los repuestos con cantidad <= stock minimo y sus 4 campos."""
    ruta = crear_db_temporal()
    try:
        insertar_repuestos(ruta, inventario)
        respuesta = cliente_con_mcp(McpEspia(ruta_db=ruta)).get("/alertas")

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        esperadas = {
            codigo: (nombre, cantidad, minimo)
            for codigo, nombre, _, minimo, cantidad in inventario
            if cantidad <= minimo
        }
        obtenidas = {a["codigo"]: (a["nombre"], a["cantidad"], a["stock_minimo"]) for a in cuerpo["alertas"]}
        assert obtenidas == esperadas
        for alerta in cuerpo["alertas"]:
            assert set(alerta) == {"nombre", "codigo", "cantidad", "stock_minimo"}
        if not esperadas:
            assert cuerpo["mensaje"] == "No hay alertas de stock activas"
    finally:
        eliminar_db(ruta)


def test_alertas_mcp_no_disponible(cliente_con_mcp):
    respuesta = cliente_con_mcp(McpEspia(caido=True)).get("/alertas")
    assert respuesta.status_code == 503
    assert respuesta.json()["detail"] == "El servicio de inventario no está disponible en este momento"

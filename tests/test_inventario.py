# Historia: H-03
"""
Pruebas del Modulo Inventario (Requisito 3): propiedades 7, 8, 9 y 10.
"""

import sqlite3

from hypothesis import assume, given, strategies as st

from tests.conftest import McpEspia, crear_db_temporal, eliminar_db, insertar_repuestos

PALABRAS = ["filtro", "aceite", "bujia", "freno", "pastilla", "disco", "correa", "faro", "motor", "radiador"]
UNIDADES = ["unidad", "litro", "juego", "par"]

estrategia_inventario = st.lists(
    st.tuples(
        st.lists(st.sampled_from(PALABRAS), min_size=1, max_size=3).map(" ".join),
        st.sampled_from(UNIDADES),
        st.integers(min_value=0, max_value=50),
        st.integers(min_value=0, max_value=500),
    ),
    min_size=1,
    max_size=15,
).map(lambda filas: [(f"REP-{i:03d}", n, u, m, c) for i, (n, u, m, c) in enumerate(filas, start=1)])


def leer_cantidades(ruta: str) -> dict:
    with sqlite3.connect(ruta) as conexion:
        return dict(
            conexion.execute(
                "SELECT r.codigo, s.cantidad FROM repuestos r JOIN stock s ON r.id = s.id_repuesto;"
            ).fetchall()
        )


# Feature: asistente-taller-jorge-motors, Propiedad 7: Completitud e inmutabilidad de la consulta de stock
# Valida: Requisito 3.2
# Feature: asistente-taller-jorge-motors, Propiedad 8: Exactitud de búsqueda por código de repuesto
# Valida: Requisito 3.3
@given(inventario=estrategia_inventario, data=st.data())
def test_propiedades_7_y_8_consulta_por_codigo(cliente_con_mcp, inventario, data):
    """Por codigo: un unico resultado exacto, con los 4 campos, sin modificar el stock."""
    ruta = crear_db_temporal()
    try:
        insertar_repuestos(ruta, inventario)
        cliente = cliente_con_mcp(McpEspia(ruta_db=ruta))
        codigo, nombre, unidad, _, cantidad = data.draw(st.sampled_from(inventario))
        antes = leer_cantidades(ruta)

        respuesta = cliente.get("/inventario", params={"q": codigo})

        assert respuesta.status_code == 200
        resultados = respuesta.json()["resultados"]
        assert len(resultados) == 1
        assert set(resultados[0]) == {"nombre", "codigo", "cantidad", "unidad"}
        assert resultados[0] == {"nombre": nombre, "codigo": codigo, "cantidad": cantidad, "unidad": unidad}
        assert leer_cantidades(ruta) == antes
    finally:
        eliminar_db(ruta)


# Feature: asistente-taller-jorge-motors, Propiedad 9: Completitud de resultados en búsqueda por nombre de repuesto
# Valida: Requisito 3.4
@given(inventario=estrategia_inventario, termino=st.sampled_from(PALABRAS + ["FILTRO", "Freno", "ace", "or"]))
def test_propiedad_9_completitud_busqueda_por_nombre(cliente_con_mcp, inventario, termino):
    """La busqueda por nombre retorna exactamente los K repuestos cuyo nombre contiene el termino."""
    esperados = {c for c, n, _, _, _ in inventario if termino.lower() in n.lower()}
    assume(esperados)
    ruta = crear_db_temporal()
    try:
        insertar_repuestos(ruta, inventario)
        respuesta = cliente_con_mcp(McpEspia(ruta_db=ruta)).get("/inventario", params={"q": termino})

        assert respuesta.status_code == 200
        assert {r["codigo"] for r in respuesta.json()["resultados"]} == esperados
    finally:
        eliminar_db(ruta)


# Feature: asistente-taller-jorge-motors, Propiedad 10: Rechazo de consulta de stock con entrada vacía o de solo espacios
# Valida: Requisito 3.7
@given(termino=st.text(alphabet=" \t\n\r", max_size=10))
def test_propiedad_10_rechazo_entrada_vacia(cliente_con_mcp, termino):
    """Entradas vacias o de solo espacios retornan 422 sin consultar el MCP."""
    mcp = McpEspia()
    respuesta = cliente_con_mcp(mcp).get("/inventario", params={"q": termino})

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "Ingrese un nombre o código de repuesto válido"
    assert mcp.llamadas == 0


def test_inventario_repuesto_no_encontrado(cliente_con_mcp):
    ruta = crear_db_temporal(poblar=True)
    try:
        respuesta = cliente_con_mcp(McpEspia(ruta_db=ruta)).get("/inventario", params={"q": "turbo"})
        assert respuesta.status_code == 200
        assert respuesta.json() == {"resultados": [], "mensaje": "Repuesto no encontrado"}
    finally:
        eliminar_db(ruta)


def test_inventario_mcp_no_disponible(cliente_con_mcp):
    respuesta = cliente_con_mcp(McpEspia(caido=True)).get("/inventario", params={"q": "REP-001"})
    assert respuesta.status_code == 503
    assert respuesta.json()["detail"] == "El servicio de inventario no está disponible en este momento"


def test_inventario_termino_demasiado_largo(cliente_con_mcp):
    mcp = McpEspia()
    respuesta = cliente_con_mcp(mcp).get("/inventario", params={"q": "x" * 101})
    assert respuesta.status_code == 422
    assert mcp.llamadas == 0

# Historia: H-02
"""
Pruebas del Modulo Historial (Requisito 2): propiedades 4, 5 y 6.
"""

from datetime import datetime, timedelta

import pytest
from hypothesis import given, strategies as st

from tests.conftest import McpEspia, crear_db_temporal, eliminar_db, insertar_ordenes
from app.modules.ordenes.repositorio import RepositorioOT
from app.modules.ordenes.schemas import OTCrear

CAMPOS_HISTORIAL = {"id", "fecha", "motivo", "tecnico", "estado", "observaciones"}
FECHA_BASE = datetime(2025, 1, 1, 8, 0, 0)


@pytest.fixture
def ruta_db():
    ruta = crear_db_temporal()
    yield ruta
    eliminar_db(ruta)


@pytest.fixture
def ruta_db_poblada():
    ruta = crear_db_temporal(poblar=True)
    yield ruta
    eliminar_db(ruta)


# Feature: asistente-taller-jorge-motors, Propiedad 4: Límite y orden del historial de OT
# Valida: Requisito 2.1
@given(
    desfases=st.lists(st.integers(min_value=0, max_value=10_000_000), unique=True, max_size=130),
    por_dni=st.booleans(),
)
def test_propiedad_4_limite_y_orden_del_historial(cliente_con_mcp, desfases, por_dni):
    """Retorna min(N, 100) OT, las mas recientes, en orden descendente por fecha."""
    ruta = crear_db_temporal()
    try:
        fechas = [(FECHA_BASE + timedelta(seconds=d)).isoformat() for d in desfases]
        insertar_ordenes(ruta, [(f, "Luis Luna", "abierta") for f in fechas], placa="PRU-001", dni="10000099")
        cliente = cliente_con_mcp(McpEspia(ruta_db=ruta))

        respuesta = cliente.get("/historial", params={"q": "10000099" if por_dni else "PRU-001"})

        assert respuesta.status_code == 200
        obtenidas = [o["fecha"] for o in respuesta.json()["ordenes"]]
        esperadas = sorted(fechas, reverse=True)[:100]
        assert len(obtenidas) == min(len(fechas), 100)
        assert obtenidas == esperadas
        if not fechas:
            assert respuesta.json()["mensaje"] == "No se encontraron registros para ese criterio de búsqueda"
    finally:
        eliminar_db(ruta)


# Feature: asistente-taller-jorge-motors, Propiedad 5: Completitud de campos al consultar una OT del historial
# Valida: Requisito 2.2
@given(
    motivo=st.text(min_size=1, max_size=100).filter(lambda s: s.strip()),
    tecnico=st.sampled_from(["Luis Pachas", "Luis Luna", "Miguel Torres"]),
    observaciones=st.none() | st.text(max_size=100),
)
def test_propiedad_5_completitud_de_campos(cliente_con_mcp, ruta_db, motivo, tecnico, observaciones):
    """Cualquier OT almacenada se recupera con exactamente los seis campos definidos."""
    datos = OTCrear(
        nombre="Cliente Simulado", dni="10000001", placa="ABC-123", marca="Kia", modelo="Rio",
        anio=2020, kilometraje=100, motivo=motivo, tecnico=tecnico, observaciones=observaciones,
    )
    id_ot = RepositorioOT(ruta_db=ruta_db).crear_ot(datos)["id_ot"]
    cliente = cliente_con_mcp(McpEspia(ruta_db=ruta_db))

    respuesta = cliente.get(f"/historial/{id_ot}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert set(cuerpo) == CAMPOS_HISTORIAL
    assert cuerpo["id"] == id_ot
    assert cuerpo["motivo"] == datos.motivo
    assert cuerpo["tecnico"] == tecnico
    assert cuerpo["observaciones"] == (observaciones or "")


ALFANUMERICO = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
estrategia_invalida = st.one_of(
    # vacio o solo espacios
    st.text(alphabet=" \t", max_size=5),
    # mas de 8 caracteres alfanumericos (no es placa ni DNI)
    st.text(alphabet=ALFANUMERICO, min_size=9, max_size=20),
    # contiene un caracter no permitido en medio
    st.tuples(
        st.text(alphabet=ALFANUMERICO, min_size=1, max_size=4),
        st.sampled_from(list("!@#$%&*()_+=.,;:/ ñ'\"")),
        st.text(alphabet=ALFANUMERICO, min_size=1, max_size=3),
    ).map("".join),
)


# Feature: asistente-taller-jorge-motors, Propiedad 6: Rechazo de búsqueda con formato inválido
# Valida: Requisito 2.5
@given(criterio=estrategia_invalida)
def test_propiedad_6_rechazo_formato_invalido(cliente_con_mcp, criterio):
    """Una cadena que no es placa ni DNI retorna 422 sin consultar el MCP."""
    mcp = McpEspia()
    respuesta = cliente_con_mcp(mcp).get("/historial", params={"q": criterio})

    assert respuesta.status_code == 422
    assert "Formato inválido" in respuesta.json()["detail"]
    assert mcp.llamadas == 0


def test_historial_mcp_no_disponible(cliente_con_mcp):
    """Si el MCP no responde se retorna 503 con el mensaje del Requisito 2.4."""
    respuesta = cliente_con_mcp(McpEspia(caido=True)).get("/historial", params={"q": "ABC-123"})
    assert respuesta.status_code == 503
    assert respuesta.json()["detail"] == "El servicio de historial no está disponible en este momento"


def test_historial_detalle_inexistente(cliente_con_mcp, ruta_db_poblada):
    respuesta = cliente_con_mcp(McpEspia(ruta_db=ruta_db_poblada)).get("/historial/9999")
    assert respuesta.status_code == 404


@pytest.mark.parametrize("criterio", ["ABC-123", "abc123", "10000001"])
def test_historial_busqueda_valida(cliente_con_mcp, ruta_db_poblada, criterio):
    respuesta = cliente_con_mcp(McpEspia(ruta_db=ruta_db_poblada)).get("/historial", params={"q": criterio})
    assert respuesta.status_code == 200
    assert len(respuesta.json()["ordenes"]) == 1

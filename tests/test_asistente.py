# Historia: H-09
"""
Pruebas del Modulo Asistente IA (Requisito 9): propiedad 17 y degradacion controlada.
"""

import json
import sqlite3
from datetime import datetime

import pytest
from hypothesis import given, strategies as st

from tests.conftest import McpEspia, crear_db_temporal, eliminar_db
from app.modules.asistente.repositorio import RepositorioTrazabilidad, obtener_repositorio_trazabilidad
from app.shared.gemini_gateway import GeminiGateway, obtener_gateway_gemini

ROLES = ["Recepcionista", "Técnico", "Encargado_Compras", "Gerente"]


@pytest.fixture
def ruta_db():
    ruta = crear_db_temporal(poblar=True)
    yield ruta
    eliminar_db(ruta)


def crear_cliente(cliente_con_mcp, ruta, generador, mcp=None):
    return cliente_con_mcp(
        mcp or McpEspia(ruta_db=ruta),
        overrides={
            obtener_gateway_gemini: GeminiGateway(generador=generador),
            obtener_repositorio_trazabilidad: RepositorioTrazabilidad(ruta_db=ruta),
        },
    )


def leer_log(ruta):
    with sqlite3.connect(ruta) as conexion:
        conexion.row_factory = sqlite3.Row
        return [dict(f) for f in conexion.execute("SELECT * FROM trazabilidad_ia;").fetchall()]


# Feature: asistente-taller-jorge-motors, Propiedad 17: Completitud y unicidad del log de trazabilidad de IA
# Valida: Requisitos 9.1, 9.2
@given(
    consultas=st.lists(
        st.tuples(st.text(min_size=1, max_size=80).filter(lambda s: s.strip()), st.sampled_from(ROLES)),
        min_size=1,
        max_size=8,
    )
)
def test_propiedad_17_log_de_trazabilidad(cliente_con_mcp, consultas):
    """Cada consulta deja una entrada con los 6 campos y los N identificadores son distintos."""
    ruta = crear_db_temporal(poblar=True)
    try:
        cliente = crear_cliente(cliente_con_mcp, ruta, lambda prompt: "Respuesta simulada")
        ids = []
        for pregunta, rol in consultas:
            respuesta = cliente.post("/asistente", json={"pregunta": pregunta, "rol": rol})
            assert respuesta.status_code == 200
            assert respuesta.json()["asistencia"] == "Respuesta simulada"
            ids.append(respuesta.json()["id_consulta"])

        log = leer_log(ruta)
        assert len(log) == len(consultas)
        assert len({e["id"] for e in log}) == len(consultas)
        assert {e["id"] for e in log} == set(ids)
        por_id = {e["id"]: e for e in log}
        for id_consulta, (pregunta, rol) in zip(ids, consultas):
            entrada = por_id[id_consulta]
            datetime.fromisoformat(entrada["timestamp"])
            assert entrada["rol"] == rol
            assert entrada["pregunta"] == pregunta.strip()
            assert isinstance(json.loads(entrada["contexto_mcp"]), dict)
            assert entrada["respuesta"] == "Respuesta simulada"
            assert entrada["error"] is None
    finally:
        eliminar_db(ruta)


def test_asistente_degradado_cuando_gemini_falla(cliente_con_mcp, ruta_db):
    """Si Gemini falla: 200 con asistencia null, mensaje y error registrado (Requisito 9.3)."""

    def falla(prompt):
        raise ConnectionError("Servicio Gemini caido")

    respuesta = crear_cliente(cliente_con_mcp, ruta_db, falla).post(
        "/asistente", json={"pregunta": "¿Hay filtros de aceite?", "rol": "Técnico"}
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["asistencia"] is None
    assert cuerpo["mensaje"] == "Asistencia de IA no disponible en este momento"

    entrada = RepositorioTrazabilidad(ruta_db=ruta_db).obtener(cuerpo["id_consulta"])
    assert entrada["pregunta"] == "¿Hay filtros de aceite?"
    assert entrada["error"] == "Servicio Gemini caido"
    assert entrada["respuesta"] is None
    datetime.fromisoformat(entrada["timestamp"])


def test_asistente_incluye_contexto_mcp_en_el_prompt(cliente_con_mcp, ruta_db):
    """El prompt enviado a Gemini incluye los datos del MCP relevantes a la pregunta."""
    prompts = []

    def captura(prompt):
        prompts.append(prompt)
        return "ok"

    crear_cliente(cliente_con_mcp, ruta_db, captura).post(
        "/asistente", json={"pregunta": "Historial de la placa ABC-123 y stock de bujia", "rol": "Técnico"}
    )
    assert "Bujia de iridio" in prompts[0]
    assert "Mantenimiento preventivo 45k" in prompts[0]


def test_asistente_funciona_sin_mcp(cliente_con_mcp, ruta_db):
    """Si el MCP no esta disponible, el asistente sigue respondiendo y lo registra en el contexto."""
    respuesta = crear_cliente(cliente_con_mcp, ruta_db, lambda p: "ok", mcp=McpEspia(caido=True)).post(
        "/asistente", json={"pregunta": "stock de filtros", "rol": "Gerente"}
    )
    assert respuesta.status_code == 200
    entrada = RepositorioTrazabilidad(ruta_db=ruta_db).obtener(respuesta.json()["id_consulta"])
    assert "error_mcp" in json.loads(entrada["contexto_mcp"])


@pytest.mark.parametrize("cuerpo", [{"pregunta": "hola", "rol": "Cliente"}, {"pregunta": "", "rol": "Gerente"}])
def test_asistente_rechaza_rol_o_pregunta_invalidos(cliente_con_mcp, ruta_db, cuerpo):
    respuesta = crear_cliente(cliente_con_mcp, ruta_db, lambda p: "ok").post("/asistente", json=cuerpo)
    assert respuesta.status_code == 422

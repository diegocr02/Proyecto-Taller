# Historia: H-09
"""
Pruebas del Modulo Asistente IA (Requisito 9): propiedad 17, degradacion controlada,
memoria por sesion y herramientas usadas. El agente usa un modelo falso (sin llamar a la API real).
"""

import json
import sqlite3
from datetime import datetime

import pytest
from hypothesis import given, strategies as st

from tests.conftest import McpEspia, crear_db_temporal, eliminar_db
from agente.agente import AgenteTaller, obtener_agente
from app.modules.asistente.repositorio import RepositorioTrazabilidad, obtener_repositorio_trazabilidad

ROLES = ["Recepcionista", "Técnico", "Encargado_Compras", "Gerente"]


@pytest.fixture
def ruta_db():
    ruta = crear_db_temporal(poblar=True)
    yield ruta
    eliminar_db(ruta)


def agente_falso(responder_texto="Respuesta simulada", falla=None, herramienta=None):
    """Agente con modelo falso: opcionalmente pide una herramienta y luego responde."""
    vistos = []

    def modelo(mensajes, herramientas):
        vistos.append(mensajes)
        if falla:
            raise falla
        if herramienta and mensajes[-1]["role"] == "user":
            return {"content": None, "tool_calls": [{"id": "1", "function": {"name": herramienta, "arguments": "{}"}}]}
        return {"content": responder_texto}

    agente = AgenteTaller(
        llamar_modelo=modelo,
        ejecutar_herramienta=lambda nombre, args: json.dumps({"ok": nombre}),
        listar_herramientas=lambda: [],
    )
    agente.mensajes_vistos = vistos
    return agente


def crear_cliente(cliente_con_mcp, ruta, agente):
    return cliente_con_mcp(
        McpEspia(ruta_db=ruta),
        overrides={
            obtener_agente: agente,
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
        cliente = crear_cliente(cliente_con_mcp, ruta, agente_falso())
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


def test_asistente_degradado_cuando_el_modelo_falla(cliente_con_mcp, ruta_db):
    """Si el modelo falla: 200 con asistencia null, mensaje y error registrado (Requisito 9.3)."""
    agente = agente_falso(falla=ConnectionError("Servicio de IA caido"))
    respuesta = crear_cliente(cliente_con_mcp, ruta_db, agente).post(
        "/asistente", json={"pregunta": "¿Hay filtros de aceite?", "rol": "Técnico"}
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["asistencia"] is None
    assert cuerpo["mensaje"] == "Asistencia de IA no disponible en este momento"

    entrada = RepositorioTrazabilidad(ruta_db=ruta_db).obtener(cuerpo["id_consulta"])
    assert entrada["pregunta"] == "¿Hay filtros de aceite?"
    assert entrada["error"] == "Servicio de IA caido"
    assert entrada["respuesta"] is None
    datetime.fromisoformat(entrada["timestamp"])


def test_asistente_informa_y_registra_la_herramienta_usada(cliente_con_mcp, ruta_db):
    """Cuando el modelo pide una herramienta, la respuesta y la trazabilidad la indican."""
    agente = agente_falso(responder_texto="Quedan 12 bujias", herramienta="buscar_repuesto")
    respuesta = crear_cliente(cliente_con_mcp, ruta_db, agente).post(
        "/asistente", json={"pregunta": "¿Hay bujias?", "rol": "Técnico"}
    )
    cuerpo = respuesta.json()
    assert cuerpo["asistencia"] == "Quedan 12 bujias"
    assert cuerpo["herramientas"] == ["buscar_repuesto"]
    contexto = json.loads(RepositorioTrazabilidad(ruta_db=ruta_db).obtener(cuerpo["id_consulta"])["contexto_mcp"])
    assert contexto["herramientas"][0]["nombre"] == "buscar_repuesto"


def test_asistente_recuerda_la_conversacion_de_la_misma_sesion(cliente_con_mcp, ruta_db):
    """Con el mismo identificador de sesion, el modelo recibe las preguntas anteriores."""
    agente = agente_falso()
    cliente = crear_cliente(cliente_con_mcp, ruta_db, agente)
    cliente.post("/asistente", json={"pregunta": "¿Cuántas baterías quedan?", "rol": "Gerente", "sesion": "abc"})
    cliente.post("/asistente", json={"pregunta": "¿Y cuál es el mínimo?", "rol": "Gerente", "sesion": "abc"})
    textos = [m["content"] for m in agente.mensajes_vistos[-1]]
    assert "¿Cuántas baterías quedan?" in textos

    # Otra sesion empieza sin memoria, y borrar la conversacion la olvida
    cliente.post("/asistente", json={"pregunta": "Hola", "rol": "Gerente", "sesion": "otra"})
    assert "¿Cuántas baterías quedan?" not in [m["content"] for m in agente.mensajes_vistos[-1]]
    assert cliente.delete("/asistente/sesion/abc?rol=Gerente").status_code == 204
    cliente.post("/asistente", json={"pregunta": "¿Y?", "rol": "Gerente", "sesion": "abc"})
    assert "¿Cuántas baterías quedan?" not in [m["content"] for m in agente.mensajes_vistos[-1]]


@pytest.mark.parametrize("cuerpo", [{"pregunta": "hola", "rol": "Cliente"}, {"pregunta": "", "rol": "Gerente"}])
def test_asistente_rechaza_rol_o_pregunta_invalidos(cliente_con_mcp, ruta_db, cuerpo):
    respuesta = crear_cliente(cliente_con_mcp, ruta_db, agente_falso()).post("/asistente", json=cuerpo)
    assert respuesta.status_code == 422

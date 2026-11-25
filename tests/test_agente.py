# Historia: H-09 (proyecto final: agente con herramientas MCP)
"""
Pruebas del servidor MCP (herramientas sobre la base simulada) y del ciclo del agente.
No llaman a ninguna API de IA real.
"""

import json
import sqlite3

import pytest

from tests.conftest import crear_db_temporal, eliminar_db
from agente import servidor_mcp as s
from agente.agente import AgenteTaller, ConexionMCP


@pytest.fixture
def base(monkeypatch):
    ruta = crear_db_temporal(poblar=True)
    monkeypatch.setenv("TALLER_DB", ruta)
    yield ruta
    eliminar_db(ruta)


def test_buscar_repuesto_por_nombre_plural_y_sin_tildes(base):
    resultado = s.buscar_repuesto("baterías")
    assert resultado["repuestos"][0]["codigo"] == "REP-009"
    assert resultado["repuestos"][0]["requiere_reposicion"] is True


def test_buscar_repuesto_por_codigo_y_no_encontrado(base):
    assert s.buscar_repuesto("REP-004")["repuestos"][0]["nombre"] == "Bujia de iridio"
    assert s.buscar_repuesto("turbo") == {"busqueda": "turbo", "encontrados": 0, "repuestos": []}


def test_repuestos_por_reponer_coincide_con_la_base(base):
    with sqlite3.connect(base) as conexion:
        esperados = {
            fila[0]
            for fila in conexion.execute(
                "SELECT r.codigo FROM repuestos r JOIN stock s ON s.id_repuesto = r.id WHERE s.cantidad <= r.stock_minimo"
            )
        }
    resultado = s.repuestos_por_reponer()
    assert {r["codigo"] for r in resultado["repuestos"]} == esperados
    assert resultado["repuestos"][0]["cantidad"] == 0  # el mas critico primero (agotado)


def test_historial_vehiculo_acepta_placa_sin_guion(base):
    resultado = s.historial_vehiculo("abc123")
    assert resultado["vehiculo"]["modelo"] == "Corolla"
    assert "Mantenimiento preventivo 45k" in [o["motivo"] for o in resultado["ordenes"]]
    assert s.historial_vehiculo("ZZZ-999")["encontrado"] is False


def test_historial_cliente_no_expone_nombre_ni_dni_ajenos(base):
    resultado = s.historial_cliente("10000002")
    assert resultado["encontrado"] is True
    assert "Ruido al frenar" in [o["motivo"] for o in resultado["ordenes"]]
    assert "Cliente Simulado" not in json.dumps(resultado)
    assert s.historial_cliente("123")["encontrado"] is False


def test_ordenes_pendientes_excluye_cerradas_y_filtra_tecnico(base):
    todas = s.ordenes_pendientes()["ordenes"]
    assert todas and all(o["estado"] != "cerrada" for o in todas)
    assert all(o["tecnico"] == "Luis Luna" for o in s.ordenes_pendientes("luna")["ordenes"])


def test_resumen_por_tecnico_y_fechas_invalidas(base):
    resultado = s.resumen_ordenes_por_tecnico("2000-01-01", "2100-12-31")
    with sqlite3.connect(base) as conexion:
        total = conexion.execute("SELECT COUNT(*) FROM ordenes_trabajo").fetchone()[0]
    assert resultado["total_ordenes"] == total
    assert "error" in s.resumen_ordenes_por_tecnico("ayer", "hoy")


def test_herramientas_son_de_solo_lectura(base):
    with pytest.raises(sqlite3.OperationalError):
        s.consultar("DELETE FROM repuestos")


def test_servidor_mcp_real_expone_al_menos_dos_herramientas(base):
    """Enciende el servidor MCP por stdio, como lo hace el agente, y ejecuta una herramienta."""
    conexion = ConexionMCP()
    nombres = {h.name for h in conexion.listar_herramientas(espera=30)}
    assert {"buscar_repuesto", "repuestos_por_reponer", "historial_vehiculo"} <= nombres
    assert "REP-004" in conexion.ejecutar("buscar_repuesto", {"texto": "bujia"})


def test_ciclo_del_agente_ejecuta_la_herramienta_y_entrega_el_dato_al_modelo():
    llamadas = []

    def modelo(mensajes, herramientas):
        if mensajes[-1]["role"] == "user":
            return {"content": None, "tool_calls": [
                {"id": "c1", "function": {"name": "buscar_repuesto", "arguments": '{"texto": "bujia"}'}}
            ]}
        assert mensajes[-1] == {"role": "tool", "tool_call_id": "c1", "content": '{"cantidad": 12}'}
        return {"content": "Quedan 12 bujías."}

    def ejecutar(nombre, argumentos):
        llamadas.append((nombre, argumentos))
        return '{"cantidad": 12}'

    agente = AgenteTaller(llamar_modelo=modelo, ejecutar_herramienta=ejecutar, listar_herramientas=lambda: [])
    resultado = agente.responder("s1", "Técnico", "¿Hay bujías?")
    assert resultado.respuesta == "Quedan 12 bujías."
    assert llamadas == [("buscar_repuesto", {"texto": "bujia"})]
    assert resultado.herramientas_usadas == [{"nombre": "buscar_repuesto", "argumentos": {"texto": "bujia"}}]


def test_agente_incluye_instrucciones_y_rol_en_el_mensaje_de_sistema():
    vistos = []
    agente = AgenteTaller(
        llamar_modelo=lambda m, h: vistos.append(m) or {"content": "Hola"},
        ejecutar_herramienta=lambda n, a: "",
        listar_herramientas=lambda: [],
    )
    agente.responder("s1", "Encargado_Compras", "Hola")
    sistema = vistos[0][0]["content"]
    assert "Eres JorgeBot" in sistema and "inteligencia artificial" in sistema
    assert "Encargado Compras" in sistema

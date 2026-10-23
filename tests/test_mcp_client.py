# Historia: H-02, H-03, H-04, H-05, H-06
"""
Pruebas unitarias para McpReadClient (Modulo Compartido).
Verifica operacion en lectura y manejo de caida con McpNoDisponibleError.
"""

import os
import tempfile
import pytest

from data.seed import inicializar_base_datos, poblar_datos_simulados
from app.shared.mcp_client import McpReadClient, McpNoDisponibleError


@pytest.fixture
def cliente_mcp_con_datos():
    """Crea una base de datos poblada temporal y retorna un McpReadClient apuntando a ella."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        ruta_db = tmp.name

    inicializar_base_datos(ruta_db)
    poblar_datos_simulados(ruta_db)

    cliente = McpReadClient(usar_stub=True, ruta_db=ruta_db)
    yield cliente

    if os.path.exists(ruta_db):
        try:
            os.remove(ruta_db)
        except OSError:
            pass


def test_mcp_buscar_historial_por_placa(cliente_mcp_con_datos):
    """Verifica que el cliente MCP recupera el historial por placa con los campos correctos."""
    historial = cliente_mcp_con_datos.buscar_historial("ABC-123", tipo="placa")
    assert isinstance(historial, list)
    assert len(historial) >= 1
    primero = historial[0]
    assert "id" in primero
    assert "fecha" in primero
    assert "motivo" in primero
    assert "tecnico" in primero
    assert "estado" in primero
    assert "observaciones" in primero


def test_mcp_buscar_historial_por_dni(cliente_mcp_con_datos):
    """Verifica que el cliente MCP recupera el historial por DNI."""
    historial = cliente_mcp_con_datos.buscar_historial("10000001", tipo="dni")
    assert isinstance(historial, list)
    assert len(historial) >= 1
    assert historial[0]["tecnico"] == "Luis Pachas"


def test_mcp_consultar_stock_codigo_exacto(cliente_mcp_con_datos):
    """Verifica que la busqueda por codigo exacto retorna el repuesto correspondiente."""
    resultados = cliente_mcp_con_datos.consultar_stock("REP-001")
    assert len(resultados) == 1
    assert resultados[0]["codigo"] == "REP-001"
    assert "Pastillas" in resultados[0]["nombre"]
    assert resultados[0]["cantidad"] == 3


def test_mcp_consultar_stock_por_nombre(cliente_mcp_con_datos):
    """Verifica la busqueda por coincidencia parcial de nombre."""
    resultados = cliente_mcp_con_datos.consultar_stock("aceite")
    assert len(resultados) >= 1
    codigos = [r["codigo"] for r in resultados]
    assert "REP-002" in codigos or "REP-003" in codigos


def test_mcp_listar_alertas_stock_minimo(cliente_mcp_con_datos):
    """Verifica que solo se listen repuestos con cantidad menor o igual a stock minimo."""
    alertas = cliente_mcp_con_datos.listar_alertas()
    assert len(alertas) > 0
    for a in alertas:
        assert a["cantidad"] <= a["stock_minimo"]


def test_mcp_comparar_conteo_fisico(cliente_mcp_con_datos):
    """Verifica calculo de diferencia y descuadre entre conteo fisico y sistema."""
    # REP-001 tiene 3 en sistema. Conteo 5 -> diferencia +2, descuadre True
    items = [
        {"codigo": "REP-001", "conteo_fisico": 5},
        {"codigo": "REP-002", "conteo_fisico": 15},  # REP-002 tiene 15 -> diferencia 0, descuadre False
    ]
    comparaciones = cliente_mcp_con_datos.comparar_conteo(items)
    assert len(comparaciones) == 2

    c1 = next(c for c in comparaciones if c["codigo"] == "REP-001")
    assert c1["sistema"] == 3
    assert c1["conteo"] == 5
    assert c1["diferencia"] == 2
    assert c1["descuadre"] is True

    c2 = next(c for c in comparaciones if c["codigo"] == "REP-002")
    assert c2["sistema"] == 15
    assert c2["conteo"] == 15
    assert c2["diferencia"] == 0
    assert c2["descuadre"] is False


def test_mcp_no_disponible_eleva_excepcion():
    """Verifica que al simular caida del MCP se eleva McpNoDisponibleError (Requisito 2.4, 3.6, etc)."""
    cliente_caido = McpReadClient(simular_error_conexion=True)
    with pytest.raises(McpNoDisponibleError):
        cliente_caido.buscar_historial("ABC-123")

    with pytest.raises(McpNoDisponibleError):
        cliente_caido.consultar_stock("REP-001")

    with pytest.raises(McpNoDisponibleError):
        cliente_caido.listar_alertas()

    with pytest.raises(McpNoDisponibleError):
        cliente_caido.comparar_conteo([{"codigo": "REP-001", "conteo_fisico": 1}])

    with pytest.raises(McpNoDisponibleError):
        cliente_caido.generar_reporte("2026-01-01", "2026-12-31")

    with pytest.raises(McpNoDisponibleError):
        cliente_caido.obtener_ot(1)


def test_mcp_servidor_real_no_configurado_eleva_excepcion(cliente_mcp_con_datos):
    """Sin stub (MCP real aun no conectado) toda lectura eleva McpNoDisponibleError."""
    cliente_real = McpReadClient(usar_stub=False, ruta_db=cliente_mcp_con_datos.ruta_db)
    with pytest.raises(McpNoDisponibleError):
        cliente_real.consultar_stock("REP-001")


def test_mcp_buscar_historial_placa_sin_guion(cliente_mcp_con_datos):
    """La placa se encuentra con o sin guion y sin distinguir mayusculas."""
    assert len(cliente_mcp_con_datos.buscar_historial("abc123", tipo="placa")) == 1


def test_mcp_obtener_ot(cliente_mcp_con_datos):
    """Recupera una OT por id con los seis campos, y None si no existe."""
    ot = cliente_mcp_con_datos.obtener_ot(1)
    assert set(ot) == {"id", "fecha", "motivo", "tecnico", "estado", "observaciones"}
    assert cliente_mcp_con_datos.obtener_ot(9999) is None


def test_mcp_generar_reporte(cliente_mcp_con_datos):
    """El reporte agrupa por tecnico con totales consistentes."""
    reporte = cliente_mcp_con_datos.generar_reporte("2000-01-01", "2099-12-31")
    assert {f["tecnico"] for f in reporte} == {"Luis Pachas", "Luis Luna", "Miguel Torres"}
    for f in reporte:
        assert f["abierta"] + f["en_proceso"] + f["cerrada"] == f["total"]


def test_mcp_consultar_stock_comodines_literales(cliente_mcp_con_datos):
    """Los caracteres % y _ se buscan de forma literal, no como comodines."""
    assert cliente_mcp_con_datos.consultar_stock("%") == []
    assert cliente_mcp_con_datos.consultar_stock("_") == []

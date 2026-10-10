# Historia: H-07
"""
Prueba de humo de rendimiento para R7.1 (tarea 14.1):
100 peticiones consecutivas a /historial y /inventario con un usuario; el p95 debe ser <= 5 s.
Usa el stub del MCP sobre una base temporal (el Servidor MCP real se conecta en la semana 4).
"""

import statistics
import time

import pytest

from tests.conftest import McpEspia, crear_db_temporal, eliminar_db

PETICIONES = 100
LIMITE_P95_S = 5.0


def medir_p95(cliente, url, params):
    tiempos = []
    for _ in range(PETICIONES):
        inicio = time.perf_counter()
        respuesta = cliente.get(url, params=params)
        tiempos.append(time.perf_counter() - inicio)
        assert respuesta.status_code == 200
    return statistics.quantiles(tiempos, n=100)[94]


@pytest.mark.parametrize(
    "url,params",
    [("/historial", {"q": "ABC-123"}), ("/inventario", {"q": "aceite"})],
)
def test_rendimiento_p95(cliente_con_mcp, url, params):
    ruta = crear_db_temporal(poblar=True)
    try:
        p95 = medir_p95(cliente_con_mcp(McpEspia(ruta_db=ruta)), url, params)
        assert p95 <= LIMITE_P95_S, f"p95 de {url} = {p95:.3f} s supera {LIMITE_P95_S} s"
    finally:
        eliminar_db(ruta)

# Historia: H-06
"""
Pruebas del Modulo Reportes (Requisito 6): propiedades 14, 15 y 16.
"""

import csv
import io
from collections import Counter
from datetime import date, datetime, timedelta

from hypothesis import given, strategies as st

from tests.conftest import McpEspia, crear_db_temporal, eliminar_db, insertar_ordenes

TECNICOS = ["Luis Pachas", "Luis Luna", "Miguel Torres"]
ESTADOS = ["abierta", "en proceso", "cerrada"]
CLAVE_ESTADO = {"abierta": "abierta", "en proceso": "en_proceso", "cerrada": "cerrada"}
DIA_BASE = date(2026, 1, 1)

estrategia_ordenes = st.lists(
    st.tuples(
        st.integers(min_value=0, max_value=60),  # dia relativo
        st.integers(min_value=0, max_value=86_399),  # segundo del dia
        st.sampled_from(TECNICOS),
        st.sampled_from(ESTADOS),
    ),
    max_size=40,
)


def preparar(ordenes):
    """Crea la base con las OT generadas; retorna (ruta, lista de (dia, tecnico, estado))."""
    ruta = crear_db_temporal()
    filas, resumen = [], []
    for dia, segundo, tecnico, estado in ordenes:
        momento = datetime.combine(DIA_BASE + timedelta(days=dia), datetime.min.time()) + timedelta(seconds=segundo)
        filas.append((momento.astimezone().isoformat(timespec="seconds"), tecnico, estado))
        resumen.append((DIA_BASE + timedelta(days=dia), tecnico, estado))
    insertar_ordenes(ruta, filas)
    return ruta, resumen


def esperado(resumen, inicio, fin):
    """Calcula en Python el reporte esperado por tecnico."""
    totales = {}
    for dia, tecnico, estado in resumen:
        if inicio <= dia <= fin:
            fila = totales.setdefault(tecnico, Counter())
            fila["total"] += 1
            fila[CLAVE_ESTADO[estado]] += 1
    return {t: (c["total"], c["abierta"], c["en_proceso"], c["cerrada"]) for t, c in totales.items()}


estrategia_rango = st.tuples(st.integers(0, 60), st.integers(0, 60)).map(
    lambda p: (DIA_BASE + timedelta(days=min(p)), DIA_BASE + timedelta(days=max(p)))
)


# Feature: asistente-taller-jorge-motors, Propiedad 14: Filtrado correcto de OT por rango de fechas en el reporte
# Valida: Requisitos 6.1, 6.2
@given(ordenes=estrategia_ordenes, rango=estrategia_rango)
def test_propiedad_14_filtrado_por_rango(cliente_con_mcp, ordenes, rango):
    """Solo se cuentan las OT con fecha dentro del rango, ambos extremos inclusivos."""
    inicio, fin = rango
    ruta, resumen = preparar(ordenes)
    try:
        respuesta = cliente_con_mcp(McpEspia(ruta_db=ruta)).get(
            "/reportes", params={"fecha_inicio": inicio.isoformat(), "fecha_fin": fin.isoformat()}
        )
        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        obtenido = {f["tecnico"]: (f["total"], f["abierta"], f["en_proceso"], f["cerrada"]) for f in cuerpo["reporte"]}
        assert obtenido == esperado(resumen, inicio, fin)
        if not obtenido:
            assert cuerpo["mensaje"] == "No se encontraron órdenes de trabajo en el período indicado"
    finally:
        eliminar_db(ruta)


# Feature: asistente-taller-jorge-motors, Propiedad 15: Rechazo de rango de fechas inválido en el reporte
# Valida: Requisito 6.4
@given(
    inicio=st.dates(min_value=date(2000, 1, 2), max_value=date(2099, 12, 31)),
    dias_antes=st.integers(min_value=1, max_value=3650),
    ruta_csv=st.booleans(),
)
def test_propiedad_15_rechazo_rango_invalido(cliente_con_mcp, inicio, dias_antes, ruta_csv):
    """Si fecha_inicio > fecha_fin se retorna 422 sin consultar el MCP."""
    fin = max(inicio - timedelta(days=dias_antes), date(2000, 1, 1))
    mcp = McpEspia()
    respuesta = cliente_con_mcp(mcp).get(
        "/reportes/csv" if ruta_csv else "/reportes",
        params={"fecha_inicio": inicio.isoformat(), "fecha_fin": fin.isoformat()},
    )
    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "La fecha de inicio no puede ser posterior a la fecha de fin"
    assert mcp.llamadas == 0


# Feature: asistente-taller-jorge-motors, Propiedad 16: Completitud y consistencia del CSV exportado
# Valida: Requisito 6.5
@given(ordenes=estrategia_ordenes, rango=estrategia_rango)
def test_propiedad_16_csv_completo_y_consistente(cliente_con_mcp, ordenes, rango):
    """El CSV tiene 5 columnas y en cada fila abiertas + en proceso + cerradas = total."""
    inicio, fin = rango
    ruta, resumen = preparar(ordenes)
    try:
        respuesta = cliente_con_mcp(McpEspia(ruta_db=ruta)).get(
            "/reportes/csv", params={"fecha_inicio": inicio.isoformat(), "fecha_fin": fin.isoformat()}
        )
        assert respuesta.status_code == 200
        assert respuesta.headers["content-type"].startswith("text/csv")
        filas = list(csv.reader(io.StringIO(respuesta.content.decode("utf-8-sig"))))
        assert filas[0] == ["Técnico", "Total OT", "Abiertas", "En proceso", "Cerradas"]
        datos = {}
        for fila in filas[1:]:
            assert len(fila) == 5
            total, abiertas, en_proceso, cerradas = map(int, fila[1:])
            assert abiertas + en_proceso + cerradas == total
            datos[fila[0]] = (total, abiertas, en_proceso, cerradas)
        assert datos == esperado(resumen, inicio, fin)
    finally:
        eliminar_db(ruta)


def test_reportes_mcp_no_disponible(cliente_con_mcp):
    respuesta = cliente_con_mcp(McpEspia(caido=True)).get(
        "/reportes", params={"fecha_inicio": "2026-01-01", "fecha_fin": "2026-01-31"}
    )
    assert respuesta.status_code == 503
    assert respuesta.json()["detail"] == "El servicio de datos no está disponible en este momento"


def test_reportes_fecha_mal_formada(cliente_con_mcp):
    respuesta = cliente_con_mcp(McpEspia()).get(
        "/reportes", params={"fecha_inicio": "01/01/2026", "fecha_fin": "2026-01-31"}
    )
    assert respuesta.status_code == 422
    assert respuesta.json()["campos"] == ["fecha_inicio"]

# Historia: H-01..H-09 (configuración común de pruebas)
"""
Configuracion comun de pruebas: perfil de Hypothesis (minimo 100 iteraciones),
bases de datos temporales y dobles de prueba del cliente MCP.
"""

import os
import sqlite3
import tempfile
from typing import Iterable, Optional, Tuple

import pytest
from fastapi.testclient import TestClient
from hypothesis import HealthCheck, settings

os.environ["MODO_TEST"] = "1"
os.environ.setdefault("GEMINI_API_KEY", "clave_prueba")

from data.seed import inicializar_base_datos, poblar_datos_simulados  # noqa: E402
from app.main import app  # noqa: E402
from app.shared.mcp_client import McpNoDisponibleError, McpReadClient, obtener_cliente_mcp  # noqa: E402

settings.register_profile(
    "taller",
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
settings.load_profile("taller")


def crear_db_temporal(poblar: bool = False) -> str:
    """Crea un archivo SQLite temporal con el esquema del proyecto y retorna su ruta."""
    descriptor, ruta = tempfile.mkstemp(suffix=".db")
    os.close(descriptor)
    inicializar_base_datos(ruta)
    if poblar:
        poblar_datos_simulados(ruta)
    return ruta


def eliminar_db(ruta: str) -> None:
    """Elimina la base temporal y sus archivos WAL, ignorando bloqueos de Windows."""
    for sufijo in ("", "-wal", "-shm"):
        try:
            os.remove(ruta + sufijo)
        except OSError:
            pass


def insertar_repuestos(ruta: str, repuestos: Iterable[Tuple[str, str, str, int, int]]) -> None:
    """Inserta repuestos (codigo, nombre, unidad, stock_minimo, cantidad) con su stock."""
    with sqlite3.connect(ruta) as conexion:
        for codigo, nombre, unidad, stock_minimo, cantidad in repuestos:
            cursor = conexion.execute(
                "INSERT INTO repuestos (codigo, nombre, unidad, stock_minimo) VALUES (?, ?, ?, ?);",
                (codigo, nombre, unidad, stock_minimo),
            )
            conexion.execute(
                "INSERT INTO stock (id_repuesto, cantidad) VALUES (?, ?);",
                (cursor.lastrowid, cantidad),
            )
        conexion.commit()


def insertar_ordenes(
    ruta: str,
    ordenes: Iterable[Tuple[str, str, str]],
    placa: str = "PRU-001",
    dni: str = "10000099",
) -> None:
    """Inserta OT (fecha_hora, tecnico, estado) para un mismo cliente y vehiculo simulados."""
    with sqlite3.connect(ruta) as conexion:
        id_cliente = conexion.execute(
            "INSERT INTO clientes (nombre, dni) VALUES (?, ?);", ("Cliente Simulado", dni)
        ).lastrowid
        id_vehiculo = conexion.execute(
            "INSERT INTO vehiculos (placa, marca, modelo, anio, id_cliente) VALUES (?, ?, ?, ?, ?);",
            (placa, "Toyota", "Yaris", 2020, id_cliente),
        ).lastrowid
        conexion.executemany(
            """
            INSERT INTO ordenes_trabajo (
                id_vehiculo, id_cliente, kilometraje, motivo, tecnico, estado, observaciones, fecha_hora
            ) VALUES (?, ?, 1000, 'Revision', ?, ?, NULL, ?);
            """,
            [(id_vehiculo, id_cliente, tecnico, estado, fecha) for fecha, tecnico, estado in ordenes],
        )
        conexion.commit()


class McpEspia(McpReadClient):
    """Cliente MCP de prueba que cuenta las llamadas y puede simular caida."""

    def __init__(self, ruta_db: Optional[str] = None, caido: bool = False):
        super().__init__(usar_stub=True, ruta_db=ruta_db, simular_error_conexion=caido)
        self.llamadas = 0

    def _verificar_disponibilidad(self) -> None:
        self.llamadas += 1
        if self.simular_error_conexion:
            raise McpNoDisponibleError("MCP simulado caido")


@pytest.fixture
def cliente_con_mcp():
    """
    Fabrica de TestClient con el cliente MCP reemplazado.
    Uso: cliente = cliente_con_mcp(mcp) ; las sobreescrituras se limpian al terminar.
    """

    def _crear(mcp: McpReadClient, **otras_dependencias) -> TestClient:
        app.dependency_overrides[obtener_cliente_mcp] = lambda: mcp
        for dependencia, valor in otras_dependencias.get("overrides", {}).items():
            app.dependency_overrides[dependencia] = (lambda v: (lambda: v))(valor)
        return TestClient(app)

    yield _crear
    app.dependency_overrides.clear()

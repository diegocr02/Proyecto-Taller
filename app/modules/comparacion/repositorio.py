# Historia: H-05
"""
Repositorio para persistir los resultados de la comparacion de conteo fisico.
Escritura directa en SQLite cumpliendo con ADR-002.
"""

import os
import sqlite3
from datetime import datetime
from typing import List, Optional
from app.modules.comparacion.schemas import ResultadoComparacion

RUTA_DB_DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "taller.db")


class RepositorioComparacion:
    """Acceso a datos de escritura para los resultados de comparacion."""

    def __init__(self, ruta_db: Optional[str] = None):
        self.ruta_db = ruta_db or RUTA_DB_DEFAULT

    def guardar_comparacion(self, resultados: List[ResultadoComparacion]) -> int:
        """Inserta cada fila de la comparacion con la misma fecha/hora. Retorna filas guardadas."""
        fecha_hora = datetime.now().astimezone().isoformat(timespec="seconds")
        filas = [
            (fecha_hora, r.codigo, r.nombre, r.sistema, r.conteo, r.diferencia, int(r.descuadre))
            for r in resultados
        ]
        with sqlite3.connect(self.ruta_db) as conexion:
            conexion.executemany(
                """
                INSERT INTO comparaciones_conteo (
                    fecha_hora, codigo, nombre, sistema, conteo, diferencia, descuadre
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                filas,
            )
            conexion.commit()
        return len(filas)


_repositorio_por_defecto = RepositorioComparacion()


def obtener_repositorio_comparacion() -> RepositorioComparacion:
    """Dependencia FastAPI: retorna el repositorio de comparaciones (se reemplaza en las pruebas)."""
    return _repositorio_por_defecto

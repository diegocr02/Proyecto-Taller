# Historia: H-09
"""
Repositorio del log de trazabilidad de consultas asistidas por IA (Requisito 9).
Escribe en la tabla trazabilidad_ia de SQLite; no se expone al MCP (ADR-003).
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

RUTA_DB_DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "taller.db")


class RepositorioTrazabilidad:
    """Registra y recupera las interacciones con la IA."""

    def __init__(self, ruta_db: Optional[str] = None):
        self.ruta_db = ruta_db or RUTA_DB_DEFAULT

    def registrar(
        self,
        rol: str,
        pregunta: str,
        contexto_mcp: Dict[str, Any],
        respuesta: Optional[str] = None,
        error: Optional[str] = None,
    ) -> str:
        """Inserta una entrada con UUID v4 y marca de tiempo ISO 8601. Retorna el id."""
        id_entrada = str(uuid.uuid4())
        marca_tiempo = datetime.now().astimezone().isoformat(timespec="seconds")
        with sqlite3.connect(self.ruta_db) as conexion:
            conexion.execute(
                """
                INSERT INTO trazabilidad_ia (id, timestamp, rol, pregunta, contexto_mcp, respuesta, error)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    id_entrada,
                    marca_tiempo,
                    rol,
                    pregunta,
                    json.dumps(contexto_mcp, ensure_ascii=False),
                    respuesta,
                    error,
                ),
            )
            conexion.commit()
        return id_entrada

    def obtener(self, id_entrada: str) -> Optional[Dict[str, Any]]:
        """Recupera la interaccion completa por su identificador (Requisito 9.2)."""
        with sqlite3.connect(self.ruta_db) as conexion:
            conexion.row_factory = sqlite3.Row
            fila = conexion.execute(
                "SELECT * FROM trazabilidad_ia WHERE id = ?;", (id_entrada,)
            ).fetchone()
        return dict(fila) if fila else None


_repositorio_por_defecto = RepositorioTrazabilidad()


def obtener_repositorio_trazabilidad() -> RepositorioTrazabilidad:
    """Dependencia FastAPI: retorna el repositorio de trazabilidad (se reemplaza en las pruebas)."""
    return _repositorio_por_defecto

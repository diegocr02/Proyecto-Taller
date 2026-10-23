# Historia: H-03
"""
Esquemas Pydantic para el modulo de Inventario (consulta de stock).
"""

from typing import List, Optional
from pydantic import BaseModel


class Repuesto(BaseModel):
    """Repuesto con exactamente los cuatro campos del Requisito 3.2."""

    nombre: str
    codigo: str
    cantidad: int
    unidad: str


class RespuestaInventario(BaseModel):
    """Respuesta de la consulta de stock."""

    resultados: List[Repuesto]
    mensaje: Optional[str] = None

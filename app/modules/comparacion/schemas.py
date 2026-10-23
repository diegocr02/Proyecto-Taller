# Historia: H-05
"""
Esquemas Pydantic para el modulo de Comparacion de conteo fisico (Requisito 5).
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ItemConteo(BaseModel):
    """Conteo fisico ingresado para un repuesto."""

    codigo: str = Field(..., min_length=1, max_length=20, description="Codigo del repuesto")
    conteo_fisico: int = Field(..., ge=0, description="Cantidad contada fisicamente")


class SolicitudComparacion(BaseModel):
    """Solicitud de comparacion; la validacion de minimo un item se hace en el router."""

    items: List[ItemConteo] = Field(default_factory=list)


class ResultadoComparacion(BaseModel):
    """Fila del resultado de la comparacion (Requisito 5.2 y 5.3)."""

    nombre: str
    codigo: str
    sistema: int
    conteo: int
    diferencia: int
    descuadre: bool


class RespuestaComparacion(BaseModel):
    """Resultados de la comparacion y mensaje de repuestos no encontrados."""

    resultados: List[ResultadoComparacion]
    no_encontrados: List[str] = Field(default_factory=list)
    mensaje: Optional[str] = None

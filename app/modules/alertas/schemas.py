# Historia: H-04
"""
Esquemas Pydantic para el modulo de Alertas de stock minimo.
"""

from typing import List, Optional
from pydantic import BaseModel


class Alerta(BaseModel):
    """Alerta de stock minimo con los campos del Requisito 4.2."""

    nombre: str
    codigo: str
    cantidad: int
    stock_minimo: int


class RespuestaAlertas(BaseModel):
    """Lista consolidada de alertas activas."""

    alertas: List[Alerta]
    mensaje: Optional[str] = None

# Historia: H-06
"""
Esquemas Pydantic para el modulo de Reportes de OT por tecnico (Requisito 6).
"""

from typing import List, Optional
from pydantic import BaseModel


class FilaReporte(BaseModel):
    """Totales de OT de un tecnico en el periodo, por estado."""

    tecnico: str
    total: int
    abierta: int
    en_proceso: int
    cerrada: int


class RespuestaReporte(BaseModel):
    """Reporte agrupado por tecnico."""

    reporte: List[FilaReporte]
    mensaje: Optional[str] = None


COLUMNAS_CSV = ["Técnico", "Total OT", "Abiertas", "En proceso", "Cerradas"]

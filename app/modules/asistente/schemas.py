# Historia: H-09
"""
Esquemas Pydantic para el modulo de Asistente IA (Requisito 9).
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field

Rol = Literal["Recepcionista", "Técnico", "Encargado_Compras", "Gerente"]


class ConsultaAsistente(BaseModel):
    """Pregunta enviada al asistente junto con el rol del usuario."""

    pregunta: str = Field(..., min_length=1, max_length=500, description="Pregunta del usuario")
    rol: Rol


class RespuestaAsistente(BaseModel):
    """Respuesta del asistente; asistencia es null cuando la IA no esta disponible."""

    id_consulta: str
    asistencia: Optional[str] = None
    mensaje: Optional[str] = None

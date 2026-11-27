# Historia: H-09
"""
Esquemas Pydantic para el modulo de Asistente IA (Requisito 9).
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

Rol = Literal["Recepcionista", "Técnico", "Encargado_Compras", "Gerente"]


class ConsultaAsistente(BaseModel):
    """Pregunta enviada al asistente junto con el rol del usuario."""

    pregunta: str = Field(..., min_length=1, max_length=500, description="Pregunta del usuario")
    rol: Rol
    sesion: Optional[str] = Field(default=None, max_length=64, description="Identificador de la conversacion (memoria)")

    @field_validator("pregunta")
    @classmethod
    def validar_pregunta(cls, v: str) -> str:
        """Una pregunta de solo espacios se rechaza (antes llegaba vacia al agente)."""
        v = v.strip()
        if not v:
            raise ValueError("La pregunta no puede estar vacía")
        return v


class RespuestaAsistente(BaseModel):
    """Respuesta del asistente; asistencia es null cuando la IA no esta disponible."""

    id_consulta: str
    asistencia: Optional[str] = None
    mensaje: Optional[str] = None
    herramientas: List[str] = Field(default_factory=list, description="Herramientas MCP que uso el agente")

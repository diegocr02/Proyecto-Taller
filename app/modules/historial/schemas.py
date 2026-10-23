# Historia: H-02
"""
Esquemas Pydantic para el modulo de Historial de clientes y vehiculos.
"""

import re
from typing import List, Optional
from pydantic import BaseModel

PATRON_DNI = re.compile(r"^[0-9]{8}$")
PATRON_PLACA = re.compile(r"^[A-Za-z0-9]{1,8}$")

MENSAJE_FORMATO_INVALIDO = (
    "Formato inválido. Use placa (máx. 8 car. alfanuméricos) o DNI (8 dígitos)"
)


def clasificar_criterio(criterio: str) -> Optional[str]:
    """
    Determina si el criterio es un DNI o una placa segun Requisito 2.5.
    Los guiones de la placa se aceptan como separadores (ej. ABC-123) y no cuentan
    para el limite de 8 caracteres alfanumericos.
    Retorna "dni", "placa" o None si el formato no es valido.
    """
    if PATRON_DNI.match(criterio):
        return "dni"
    if PATRON_PLACA.match(criterio.replace("-", "")):
        return "placa"
    return None


class OTHistorial(BaseModel):
    """OT del historial con exactamente los seis campos del Requisito 2.2."""

    id: int
    fecha: str
    motivo: str
    tecnico: str
    estado: str
    observaciones: str


class RespuestaHistorial(BaseModel):
    """Respuesta de la busqueda de historial (hasta 100 OT)."""

    ordenes: List[OTHistorial]
    mensaje: Optional[str] = None

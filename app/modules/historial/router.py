# Historia: H-02
"""
Router para los endpoints del modulo de Historial (Requisito 2).
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.modules.historial.schemas import (
    MENSAJE_FORMATO_INVALIDO,
    OTHistorial,
    RespuestaHistorial,
    clasificar_criterio,
)
from app.shared.mcp_client import McpNoDisponibleError, McpReadClient, obtener_cliente_mcp

router = APIRouter(prefix="/historial", tags=["Historial"])
logger = logging.getLogger("asistente_taller")

MENSAJE_MCP_NO_DISPONIBLE = "El servicio de historial no está disponible en este momento"


@router.get("", response_model=RespuestaHistorial)
def buscar_historial(
    q: str = "", mcp: McpReadClient = Depends(obtener_cliente_mcp)
) -> RespuestaHistorial:
    """Busca las hasta 100 OT mas recientes por placa o DNI."""
    criterio = q.strip()
    tipo = clasificar_criterio(criterio)
    if tipo is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MENSAJE_FORMATO_INVALIDO)

    try:
        ordenes = mcp.buscar_historial(criterio, tipo=tipo)
    except McpNoDisponibleError as e:
        logger.error("MCP no disponible en historial: %s", e.mensaje)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=MENSAJE_MCP_NO_DISPONIBLE)

    if not ordenes:
        return RespuestaHistorial(
            ordenes=[], mensaje="No se encontraron registros para ese criterio de búsqueda"
        )
    return RespuestaHistorial(ordenes=ordenes[:100])


@router.get("/{id_ot}", response_model=OTHistorial)
def obtener_ot_historial(
    id_ot: int, mcp: McpReadClient = Depends(obtener_cliente_mcp)
) -> OTHistorial:
    """Recupera una OT del historial con sus seis campos (Requisito 2.2)."""
    try:
        ot = mcp.obtener_ot(id_ot)
    except McpNoDisponibleError as e:
        logger.error("MCP no disponible en historial: %s", e.mensaje)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=MENSAJE_MCP_NO_DISPONIBLE)

    if ot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden de trabajo no encontrada")
    return ot

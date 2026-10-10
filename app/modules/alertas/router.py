# Historia: H-04
"""
Router para el endpoint del modulo de Alertas de stock minimo (Requisito 4).
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.modules.alertas.schemas import RespuestaAlertas
from app.shared.mcp_client import McpNoDisponibleError, McpReadClient, obtener_cliente_mcp

router = APIRouter(prefix="/alertas", tags=["Alertas"])
logger = logging.getLogger("asistente_taller")


@router.get("", response_model=RespuestaAlertas)
def listar_alertas(mcp: McpReadClient = Depends(obtener_cliente_mcp)) -> RespuestaAlertas:
    """Lista los repuestos cuya cantidad es menor o igual a su stock minimo."""
    try:
        alertas = mcp.listar_alertas()
    except McpNoDisponibleError as e:
        logger.error("MCP no disponible en alertas: %s", e.mensaje)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de inventario no está disponible en este momento",
        )

    if not alertas:
        return RespuestaAlertas(alertas=[], mensaje="No hay alertas de stock activas")
    return RespuestaAlertas(alertas=alertas)

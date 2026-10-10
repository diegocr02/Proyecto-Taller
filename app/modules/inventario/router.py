# Historia: H-03
"""
Router para el endpoint del modulo de Inventario (Requisito 3).
La consulta es de solo lectura: no modifica ningun dato del inventario.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.modules.inventario.schemas import RespuestaInventario
from app.shared.mcp_client import McpNoDisponibleError, McpReadClient, obtener_cliente_mcp

router = APIRouter(prefix="/inventario", tags=["Inventario"])
logger = logging.getLogger("asistente_taller")

LONGITUD_MAXIMA = 100


@router.get("", response_model=RespuestaInventario)
def consultar_stock(
    q: str = "", mcp: McpReadClient = Depends(obtener_cliente_mcp)
) -> RespuestaInventario:
    """Consulta el stock por codigo exacto o por coincidencia parcial del nombre."""
    termino = q.strip()
    if not termino:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Ingrese un nombre o código de repuesto válido",
        )
    if len(termino) > LONGITUD_MAXIMA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"El nombre o código no puede superar {LONGITUD_MAXIMA} caracteres",
        )

    try:
        resultados = mcp.consultar_stock(termino)
    except McpNoDisponibleError as e:
        logger.error("MCP no disponible en inventario: %s", e.mensaje)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de inventario no está disponible en este momento",
        )

    if not resultados:
        return RespuestaInventario(resultados=[], mensaje="Repuesto no encontrado")
    return RespuestaInventario(resultados=resultados)

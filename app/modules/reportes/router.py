# Historia: H-06
"""
Router para los endpoints del modulo de Reportes (Requisito 6).
Incluye la exportacion del reporte en formato CSV (UTF-8).
"""

import csv
import io
import logging
from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from app.modules.reportes.schemas import COLUMNAS_CSV, FilaReporte, RespuestaReporte
from app.shared.mcp_client import McpNoDisponibleError, McpReadClient, obtener_cliente_mcp

router = APIRouter(prefix="/reportes", tags=["Reportes"])
logger = logging.getLogger("asistente_taller")


def _obtener_filas(fecha_inicio: date, fecha_fin: date, mcp: McpReadClient) -> List[FilaReporte]:
    """Valida el rango (extremos inclusivos) y consulta el reporte al MCP."""
    if fecha_inicio > fecha_fin:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="La fecha de inicio no puede ser posterior a la fecha de fin",
        )
    try:
        filas = mcp.generar_reporte(fecha_inicio.isoformat(), fecha_fin.isoformat())
    except McpNoDisponibleError as e:
        logger.error("MCP no disponible en reportes: %s", e.mensaje)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de datos no está disponible en este momento",
        )
    return [FilaReporte(**f) for f in filas]


@router.get("", response_model=RespuestaReporte)
def generar_reporte(
    fecha_inicio: date, fecha_fin: date, mcp: McpReadClient = Depends(obtener_cliente_mcp)
) -> RespuestaReporte:
    """Genera el reporte de OT por tecnico en el rango de fechas."""
    filas = _obtener_filas(fecha_inicio, fecha_fin, mcp)
    if not filas:
        return RespuestaReporte(
            reporte=[], mensaje="No se encontraron órdenes de trabajo en el período indicado"
        )
    return RespuestaReporte(reporte=filas)


@router.get("/csv")
def exportar_reporte_csv(
    fecha_inicio: date, fecha_fin: date, mcp: McpReadClient = Depends(obtener_cliente_mcp)
) -> StreamingResponse:
    """Exporta el reporte en CSV UTF-8 (con BOM para que Excel muestre las tildes)."""
    filas = _obtener_filas(fecha_inicio, fecha_fin, mcp)

    buffer = io.StringIO()
    escritor = csv.writer(buffer)
    escritor.writerow(COLUMNAS_CSV)
    for f in filas:
        escritor.writerow([f.tecnico, f.total, f.abierta, f.en_proceso, f.cerrada])

    contenido = buffer.getvalue().encode("utf-8-sig")
    nombre_archivo = f"reporte_ot_{fecha_inicio.isoformat()}_{fecha_fin.isoformat()}.csv"
    return StreamingResponse(
        io.BytesIO(contenido),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )

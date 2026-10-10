# Historia: H-05
"""
Router para el endpoint del modulo de Comparacion de conteo fisico (Requisito 5).
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.modules.comparacion.schemas import (
    RespuestaComparacion,
    ResultadoComparacion,
    SolicitudComparacion,
)
from app.modules.comparacion.repositorio import RepositorioComparacion, obtener_repositorio_comparacion
from app.shared.mcp_client import McpNoDisponibleError, McpReadClient, obtener_cliente_mcp

router = APIRouter(prefix="/comparacion", tags=["Comparacion"])
logger = logging.getLogger("asistente_taller")


def calcular_resultado(nombre: str, codigo: str, sistema: int, conteo: int) -> ResultadoComparacion:
    """Calcula la diferencia con signo (conteo fisico - sistema) y el indicador de descuadre."""
    diferencia = conteo - sistema
    return ResultadoComparacion(
        nombre=nombre,
        codigo=codigo,
        sistema=sistema,
        conteo=conteo,
        diferencia=diferencia,
        descuadre=diferencia != 0,
    )


@router.post("", response_model=RespuestaComparacion)
def comparar_conteo(
    solicitud: SolicitudComparacion,
    mcp: McpReadClient = Depends(obtener_cliente_mcp),
    repositorio: RepositorioComparacion = Depends(obtener_repositorio_comparacion),
) -> RespuestaComparacion:
    """Compara el conteo fisico contra la cantidad registrada en el sistema."""
    if not solicitud.items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Debe ingresar al menos un repuesto con su conteo físico",
        )

    items = [{"codigo": i.codigo.strip(), "conteo_fisico": i.conteo_fisico} for i in solicitud.items]
    try:
        registros = mcp.comparar_conteo(items)
    except McpNoDisponibleError as e:
        logger.error("MCP no disponible en comparacion: %s", e.mensaje)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de inventario no está disponible en este momento",
        )

    sistema_por_codigo = {r["codigo"].upper(): r for r in registros}
    resultados = []
    no_encontrados = []
    for item in items:
        registro = sistema_por_codigo.get(item["codigo"].upper())
        if registro is None:
            no_encontrados.append(item["codigo"])
            continue
        resultados.append(
            calcular_resultado(registro["nombre"], registro["codigo"], registro["sistema"], item["conteo_fisico"])
        )

    if resultados:
        try:
            repositorio.guardar_comparacion(resultados)
        except Exception:
            logger.exception("No se pudo guardar el resultado de la comparacion")

    mensaje = None
    if no_encontrados:
        mensaje = "Repuesto no encontrado en el inventario: " + ", ".join(no_encontrados)
    return RespuestaComparacion(resultados=resultados, no_encontrados=no_encontrados, mensaje=mensaje)

# Historia: H-01
"""
Router para los endpoints del modulo de Ordenes de Trabajo (OT).
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.modules.ordenes.schemas import OTCrear, OTRespuesta, OTDetalle
from app.modules.ordenes.repositorio import RepositorioOT, obtener_repositorio_ot

router = APIRouter(prefix="/ordenes", tags=["Ordenes de Trabajo"])
logger = logging.getLogger("asistente_taller")


@router.post("", status_code=status.HTTP_201_CREATED, response_model=OTRespuesta)
def crear_orden_trabajo(
    datos: OTCrear, repositorio: RepositorioOT = Depends(obtener_repositorio_ot)
) -> OTRespuesta:
    """
    Crea una nueva Orden de Trabajo a partir de los datos recibidos.
    Valida campos obligatorios y persiste en SQLite.
    """
    try:
        resultado = repositorio.crear_ot(datos)
    except Exception:
        logger.exception("Error al registrar la orden de trabajo")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo registrar la orden de trabajo. Intente nuevamente.",
        )
    return OTRespuesta(id_ot=resultado["id_ot"], mensaje="OT creada exitosamente")


@router.get("/{id_ot}", response_model=OTDetalle)
def obtener_orden_trabajo(
    id_ot: str, repositorio: RepositorioOT = Depends(obtener_repositorio_ot)
) -> OTDetalle:
    """
    Recupera el detalle de una OT por su identificador.
    Solo se aceptan identificadores numericos de hasta 9 digitos; cualquier otro
    valor (texto, negativos, vacio, cadenas largas) se trata como OT inexistente: 404.
    """
    ot = None
    if id_ot.isascii() and id_ot.isdigit() and len(id_ot) <= 9:
        ot = repositorio.obtener_ot_por_id(int(id_ot))
    if not ot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de trabajo no encontrada",
        )
    return ot

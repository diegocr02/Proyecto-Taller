# Historia: H-09
"""
Router del modulo de Asistente IA (Requisito 9) - puente entre el chat y el agente JorgeBot.
Hace el papel de chat.php del instructivo: el navegador nunca habla con el modelo ni con el
servidor MCP; envia el mensaje aqui, se lo pasa al agente y registra la trazabilidad.
Si el agente falla, responde en modo degradado sin afectar al resto del sistema.
"""

import logging
import uuid
from fastapi import APIRouter, Depends
from agente.agente import AgenteTaller, obtener_agente
from app.modules.asistente.repositorio import RepositorioTrazabilidad, obtener_repositorio_trazabilidad
from app.modules.asistente.schemas import ConsultaAsistente, RespuestaAsistente

router = APIRouter(prefix="/asistente", tags=["Asistente IA"])
logger = logging.getLogger("asistente_taller")

MENSAJE_IA_NO_DISPONIBLE = "Asistencia de IA no disponible en este momento"


@router.post("", response_model=RespuestaAsistente)
def consultar_asistente(
    consulta: ConsultaAsistente,
    agente: AgenteTaller = Depends(obtener_agente),
    trazabilidad: RepositorioTrazabilidad = Depends(obtener_repositorio_trazabilidad),
) -> RespuestaAsistente:
    """Envia la pregunta al agente (que decide que herramientas MCP usar) y registra la interaccion."""
    pregunta = consulta.pregunta.strip()
    # Cada conversacion del chat tiene su propia memoria; sin sesion, la pregunta va sola
    sesion = f"{consulta.rol}:{consulta.sesion}" if consulta.sesion else f"temporal:{uuid.uuid4()}"
    resultado = agente.responder(sesion, consulta.rol, pregunta)
    if not consulta.sesion:
        agente.olvidar(sesion)
    contexto = {"herramientas": resultado.herramientas_usadas}

    if resultado.error is not None:
        id_consulta = trazabilidad.registrar(consulta.rol, pregunta, contexto, error=resultado.error)
        logger.error("Consulta IA %s sin respuesta: %s", id_consulta, resultado.error)
        return RespuestaAsistente(id_consulta=id_consulta, asistencia=None, mensaje=MENSAJE_IA_NO_DISPONIBLE)

    id_consulta = trazabilidad.registrar(consulta.rol, pregunta, contexto, respuesta=resultado.respuesta)
    return RespuestaAsistente(
        id_consulta=id_consulta,
        asistencia=resultado.respuesta,
        herramientas=[h["nombre"] for h in resultado.herramientas_usadas],
    )


@router.delete("/sesion/{sesion}", status_code=204)
def borrar_conversacion(sesion: str, rol: str, agente: AgenteTaller = Depends(obtener_agente)) -> None:
    """Borra la memoria de una conversacion (boton de papelera del chat)."""
    agente.olvidar(f"{rol}:{sesion}")

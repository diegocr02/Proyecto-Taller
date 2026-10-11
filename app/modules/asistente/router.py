# Historia: H-09
"""
Router del modulo de Asistente IA (Requisito 9).
Orquesta: contexto desde McpReadClient -> GeminiGateway -> registro de trazabilidad.
Si Gemini falla, responde en modo degradado sin afectar al resto del sistema.
"""

import json
import logging
import re
from typing import Any, Dict
from fastapi import APIRouter, Depends
from app.modules.asistente.repositorio import RepositorioTrazabilidad, obtener_repositorio_trazabilidad
from app.modules.asistente.schemas import ConsultaAsistente, RespuestaAsistente
from app.shared.gemini_gateway import GeminiError, GeminiGateway, obtener_gateway_gemini
from app.shared.mcp_client import McpNoDisponibleError, McpReadClient, obtener_cliente_mcp

router = APIRouter(prefix="/asistente", tags=["Asistente IA"])
logger = logging.getLogger("asistente_taller")

MENSAJE_IA_NO_DISPONIBLE = "Asistencia de IA no disponible en este momento"
PATRON_DNI = re.compile(r"\b\d{8}\b")
PATRON_PLACA = re.compile(r"\b[A-Za-z]{3}-?\d{3}\b")
PATRON_PALABRA = re.compile(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9-]{4,}")
MAX_REPUESTOS_CONTEXTO = 20


def obtener_contexto(pregunta: str, mcp: McpReadClient) -> Dict[str, Any]:
    """Reune datos de solo lectura del MCP relevantes para la pregunta."""
    contexto: Dict[str, Any] = {}
    try:
        contexto["alertas_stock"] = mcp.listar_alertas()

        repuestos: Dict[str, Dict[str, Any]] = {}
        for palabra in PATRON_PALABRA.findall(pregunta):
            for r in mcp.consultar_stock(palabra):
                repuestos[r["codigo"]] = r
            if len(repuestos) >= MAX_REPUESTOS_CONTEXTO:
                break
        contexto["repuestos"] = list(repuestos.values())[:MAX_REPUESTOS_CONTEXTO]

        # Cada historial va etiquetado con su criterio para que la IA sepa a quien pertenece
        historial: Dict[str, Any] = {}
        for dni in PATRON_DNI.findall(pregunta):
            historial[f"OT del cliente con DNI {dni}"] = mcp.buscar_historial(dni, tipo="dni")[:10]
        for placa in PATRON_PLACA.findall(pregunta):
            historial[f"OT del vehiculo con placa {placa.upper()}"] = mcp.buscar_historial(placa, tipo="placa")[:10]
        if historial:
            contexto["historial"] = historial
    except McpNoDisponibleError as e:
        logger.error("MCP no disponible al obtener contexto para la IA: %s", e.mensaje)
        contexto["error_mcp"] = "Servicio de datos no disponible"
    return contexto


def construir_prompt(rol: str, pregunta: str, contexto: Dict[str, Any]) -> str:
    """Arma el prompt con instrucciones, contexto del taller y la pregunta."""
    return (
        "Eres el asistente del taller mecánico Jorge Motors. Responde en español, de forma breve "
        "y clara, usando solo los datos del contexto. Si el contexto no tiene la información, "
        "dilo sin inventar datos. Escribe en texto plano, sin formato Markdown (sin asteriscos "
        "ni almohadillas); para listas usa un guion al inicio de cada línea.\n"
        "En 'alertas_stock' están todos los repuestos que requieren reposición: aquellos cuya "
        "cantidad es menor o igual a su stock mínimo. Inclúyelos todos cuando pregunten qué "
        "comprar o reponer, incluidos los que están justo en el mínimo.\n\n"
        f"Rol del usuario: {rol}\n"
        f"Contexto del sistema (solo lectura): {contexto}\n\n"
        f"Pregunta: {pregunta}"
    )


@router.post("", response_model=RespuestaAsistente)
def consultar_asistente(
    consulta: ConsultaAsistente,
    mcp: McpReadClient = Depends(obtener_cliente_mcp),
    gateway: GeminiGateway = Depends(obtener_gateway_gemini),
    trazabilidad: RepositorioTrazabilidad = Depends(obtener_repositorio_trazabilidad),
) -> RespuestaAsistente:
    """Responde una pregunta con asistencia de IA y registra la interaccion."""
    pregunta = consulta.pregunta.strip()
    contexto = obtener_contexto(pregunta, mcp)
    resultado = gateway.generar_respuesta(construir_prompt(consulta.rol, pregunta, contexto))

    if isinstance(resultado, GeminiError):
        id_consulta = trazabilidad.registrar(consulta.rol, pregunta, contexto, error=resultado.mensaje)
        logger.error("Consulta IA %s sin respuesta: %s", id_consulta, resultado.mensaje)
        return RespuestaAsistente(id_consulta=id_consulta, asistencia=None, mensaje=MENSAJE_IA_NO_DISPONIBLE)

    id_consulta = trazabilidad.registrar(consulta.rol, pregunta, contexto, respuesta=resultado.respuesta)
    return RespuestaAsistente(id_consulta=id_consulta, asistencia=resultado.respuesta)

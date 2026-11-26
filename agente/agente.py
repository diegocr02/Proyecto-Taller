# agente.py - JorgeBot: recibe un mensaje, deja que el modelo elija herramientas MCP y devuelve la respuesta
"""
Agente del proyecto final (paso 4 del instructivo, ruta B en Python).

Flujo de cada pregunta:
1. Se arma la conversacion: instrucciones.txt + memoria de la sesion + mensaje del usuario.
2. El modelo recibe la lista de herramientas del servidor MCP y DECIDE si necesita alguna.
3. Si pide una herramienta, el agente la ejecuta en el servidor MCP y le devuelve el dato.
4. El modelo redacta la respuesta final con ese dato.

Modelos compatibles (todos con la misma API de "chat completions" con herramientas):
OpenAI (OPENAI_API_KEY), Gemini (GEMINI_API_KEY) o Groq (GROQ_API_KEY, contingencia).
Las claves se leen solo de variables de entorno (.env, que no se sube a GitHub).
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
from collections import OrderedDict
from concurrent.futures import Future
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable, Dict, List, Optional

import httpx

logger = logging.getLogger("asistente_taller")

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_SERVIDOR_MCP = os.path.join(CARPETA, "servidor_mcp.py")
RUTA_INSTRUCCIONES = os.path.join(CARPETA, "instrucciones.txt")

MAX_MENSAJES_MEMORIA = 10   # ultimos mensajes que se recuerdan por conversacion
MAX_SESIONES = 200          # conversaciones guardadas en memoria a la vez
MAX_VUELTAS_HERRAMIENTAS = 4
TIEMPO_LIMITE_MODELO = 20.0  # segundos por llamada al modelo

PROVEEDORES = {
    "openai": ("OPENAI_API_KEY", "https://api.openai.com/v1", "OPENAI_MODEL", "gpt-4o-mini"),
    "gemini": ("GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_MODEL", "gemini-2.5-flash"),
    "groq": ("GROQ_API_KEY", "https://api.groq.com/openai/v1", "GROQ_MODEL", "llama-3.3-70b-versatile"),
}


def elegir_proveedor() -> Optional[str]:
    """Usa AGENTE_PROVEEDOR si esta definido; si no, el primero que tenga clave (OpenAI, Gemini, Groq)."""
    preferido = os.getenv("AGENTE_PROVEEDOR", "").strip().lower()
    if preferido in PROVEEDORES and os.getenv(PROVEEDORES[preferido][0]):
        return preferido
    for nombre, (variable_clave, *_resto) in PROVEEDORES.items():
        if os.getenv(variable_clave):
            return nombre
    return None


# ---------------------------------------------------------------------------
# Conexion permanente con el servidor MCP (por stdio)
# ---------------------------------------------------------------------------
class ConexionMCP:
    """
    Mantiene el servidor MCP encendido en un hilo propio, para no arrancarlo en cada pregunta
    (asi el agente responde mas rapido). Si el servidor se cae, se vuelve a encender solo.
    """

    def __init__(self, ruta_servidor: str = RUTA_SERVIDOR_MCP):
        self.ruta_servidor = ruta_servidor
        self._candado = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._cola: Optional[asyncio.Queue] = None
        self._listo: Optional[Future] = None
        self.herramientas: List[Any] = []

    def _iniciar(self) -> None:
        with self._candado:
            if self._listo is not None and not (self._listo.done() and self._listo.exception()):
                return
            self._listo = Future()
            listo = self._listo

            def hilo():
                loop = asyncio.new_event_loop()
                self._loop = loop
                try:
                    loop.run_until_complete(self._trabajador(listo))
                except Exception as error:  # el servidor no pudo arrancar o se cayo
                    logger.error("Servidor MCP detenido: %s", error)
                    if not listo.done():
                        listo.set_exception(error)
                finally:
                    with self._candado:
                        if self._listo is listo and listo.done() and not listo.exception():
                            self._listo = None  # la proxima consulta lo vuelve a encender
                    loop.close()

            threading.Thread(target=hilo, name="servidor-mcp", daemon=True).start()

    async def _trabajador(self, listo: Future) -> None:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        parametros = StdioServerParameters(command=sys.executable, args=[self.ruta_servidor], env=dict(os.environ))
        async with stdio_client(parametros) as (lectura, escritura):
            async with ClientSession(lectura, escritura) as sesion:
                await sesion.initialize()
                self.herramientas = (await sesion.list_tools()).tools
                self._cola = asyncio.Queue()
                listo.set_result(True)
                logger.info("Servidor MCP listo con %d herramientas", len(self.herramientas))
                while True:
                    nombre, argumentos, resultado = await self._cola.get()
                    try:
                        respuesta = await sesion.call_tool(nombre, argumentos)
                        texto = "\n".join(getattr(c, "text", "") for c in respuesta.content)
                        resultado.set_result(texto)
                    except Exception as error:
                        resultado.set_exception(error)
                        if isinstance(error, (BrokenPipeError, ConnectionError, EOFError)):
                            raise

    def listar_herramientas(self, espera: float = 15.0) -> List[Any]:
        self._iniciar()
        self._listo.result(timeout=espera)
        return self.herramientas

    def ejecutar(self, nombre: str, argumentos: Dict[str, Any], espera: float = 10.0) -> str:
        self.listar_herramientas()
        resultado: Future = Future()
        self._loop.call_soon_threadsafe(self._cola.put_nowait, (nombre, argumentos, resultado))
        return resultado.result(timeout=espera)


def herramientas_a_formato_modelo(herramientas: List[Any]) -> List[Dict[str, Any]]:
    """Convierte las herramientas MCP al formato de 'function calling' que entienden los modelos."""
    return [
        {
            "type": "function",
            "function": {
                "name": h.name,
                "description": h.description or "",
                "parameters": h.inputSchema or {"type": "object", "properties": {}},
            },
        }
        for h in herramientas
    ]


# ---------------------------------------------------------------------------
# Agente
# ---------------------------------------------------------------------------
@dataclass
class ResultadoAgente:
    respuesta: Optional[str] = None
    error: Optional[str] = None
    herramientas_usadas: List[Dict[str, Any]] = field(default_factory=list)


class AgenteTaller:
    """JorgeBot. Los parametros permiten inyectar dobles de prueba (modelo y herramientas falsas)."""

    def __init__(
        self,
        llamar_modelo: Optional[Callable[[List[Dict[str, Any]], List[Dict[str, Any]]], Dict[str, Any]]] = None,
        ejecutar_herramienta: Optional[Callable[[str, Dict[str, Any]], str]] = None,
        listar_herramientas: Optional[Callable[[], List[Dict[str, Any]]]] = None,
    ):
        self._mcp = ConexionMCP() if (ejecutar_herramienta is None or listar_herramientas is None) else None
        self._llamar_modelo = llamar_modelo or self._llamar_modelo_api
        self._ejecutar_herramienta = ejecutar_herramienta or self._mcp.ejecutar
        self._listar_herramientas = listar_herramientas or (lambda: herramientas_a_formato_modelo(self._mcp.listar_herramientas()))
        self._memoria: "OrderedDict[str, List[Dict[str, str]]]" = OrderedDict()
        self._candado = threading.Lock()
        self._cliente_http: Optional[httpx.Client] = None

    def precalentar(self) -> None:
        """Enciende el servidor MCP antes de la primera pregunta."""
        try:
            self._listar_herramientas()
        except Exception as error:
            logger.error("No se pudo encender el servidor MCP: %s", error)

    # --- memoria de cada conversacion ---
    def _historial(self, sesion: str) -> List[Dict[str, str]]:
        with self._candado:
            historial = self._memoria.setdefault(sesion, [])
            self._memoria.move_to_end(sesion)
            while len(self._memoria) > MAX_SESIONES:
                self._memoria.popitem(last=False)
            return list(historial)

    def _recordar(self, sesion: str, pregunta: str, respuesta: str) -> None:
        with self._candado:
            historial = self._memoria.setdefault(sesion, [])
            historial += [{"role": "user", "content": pregunta}, {"role": "assistant", "content": respuesta}]
            del historial[:-MAX_MENSAJES_MEMORIA]

    def olvidar(self, sesion: str) -> None:
        with self._candado:
            self._memoria.pop(sesion, None)

    # --- llamada al modelo (API compatible con OpenAI) ---
    def _llamar_modelo_api(self, mensajes: List[Dict[str, Any]], herramientas: List[Dict[str, Any]]) -> Dict[str, Any]:
        proveedor = elegir_proveedor()
        if proveedor is None:
            raise RuntimeError("Clave de API no configurada")
        variable_clave, url_base, variable_modelo, modelo_por_defecto = PROVEEDORES[proveedor]
        if self._cliente_http is None:
            self._cliente_http = httpx.Client(timeout=TIEMPO_LIMITE_MODELO)  # conexion reutilizada: mas rapido
        cuerpo = {
            "model": os.getenv(variable_modelo, modelo_por_defecto),
            "messages": mensajes,
            "temperature": 0.2,
            "max_tokens": 450,
        }
        if herramientas:
            cuerpo["tools"] = herramientas
        respuesta = self._cliente_http.post(
            f"{url_base}/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv(variable_clave)}"},
            json=cuerpo,
        )
        if respuesta.status_code != 200:
            raise RuntimeError(f"{proveedor} {respuesta.status_code}: {respuesta.text[:200]}")
        return respuesta.json()["choices"][0]["message"]

    # --- ciclo del agente ---
    def responder(self, sesion: str, rol: str, mensaje: str) -> ResultadoAgente:
        resultado = ResultadoAgente()
        inicio = time.monotonic()
        try:
            with open(RUTA_INSTRUCCIONES, encoding="utf-8") as archivo:
                instrucciones = archivo.read()
            sistema = (
                f"{instrucciones}\nDatos de la sesión: hoy es {date.today().isoformat()} "
                f"(formato AAAA-MM-DD) y el usuario tiene el rol {rol.replace('_', ' ')}."
            )
            historial = self._historial(sesion)
            mensajes: List[Dict[str, Any]] = [{"role": "system", "content": sistema}, *historial, {"role": "user", "content": mensaje}]
            herramientas = self._listar_herramientas()

            for vuelta in range(MAX_VUELTAS_HERRAMIENTAS + 1):
                # En la ultima vuelta ya no se ofrecen herramientas: el modelo debe responder
                respuesta_modelo = self._llamar_modelo(mensajes, herramientas if vuelta < MAX_VUELTAS_HERRAMIENTAS else [])
                llamadas = respuesta_modelo.get("tool_calls") or []
                if not llamadas:
                    texto = (respuesta_modelo.get("content") or "").strip()
                    if not texto:
                        raise RuntimeError("Respuesta vacia del modelo")
                    resultado.respuesta = texto
                    break
                mensajes.append({"role": "assistant", "content": respuesta_modelo.get("content"), "tool_calls": llamadas})
                for llamada in llamadas:
                    nombre = llamada["function"]["name"]
                    try:
                        argumentos = json.loads(llamada["function"].get("arguments") or "{}")
                    except json.JSONDecodeError:
                        argumentos = {}
                    logger.info("Agente usa la herramienta MCP %s %s", nombre, argumentos)
                    try:
                        dato = self._ejecutar_herramienta(nombre, argumentos)
                    except Exception as error:
                        logger.error("Fallo la herramienta %s: %s", nombre, error)
                        dato = json.dumps({"error": "La herramienta no respondió. Intente más tarde."})
                    resultado.herramientas_usadas.append({"nombre": nombre, "argumentos": argumentos})
                    mensajes.append({"role": "tool", "tool_call_id": llamada["id"], "content": dato})
        except Exception as error:
            logger.error("Error del agente: %s", error)
            resultado.error = str(error) or error.__class__.__name__
            return resultado

        self._recordar(sesion, mensaje, resultado.respuesta)
        logger.info("Agente respondio en %.2f s", time.monotonic() - inicio)
        return resultado


_agente_por_defecto: Optional[AgenteTaller] = None
_candado_agente = threading.Lock()


def obtener_agente() -> AgenteTaller:
    """Dependencia FastAPI: un solo agente compartido (se reemplaza en las pruebas)."""
    global _agente_por_defecto
    with _candado_agente:
        if _agente_por_defecto is None:
            _agente_por_defecto = AgenteTaller()
        return _agente_por_defecto

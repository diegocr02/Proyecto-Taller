# Historia: H-08, H-09
"""
GeminiGateway: unico punto de acceso a Gemini API (ADR-003).
Lee la clave exclusivamente desde la variable de entorno GEMINI_API_KEY (Requisito 8.1),
aplica un tiempo limite menor a 30 s y retorna un resultado tipado sin propagar excepciones
(degradacion controlada).
"""

import logging
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturoTimeoutError
from dataclasses import dataclass
from typing import Callable, Optional, Union

logger = logging.getLogger("asistente_taller")

TIMEOUT_POR_DEFECTO = 20.0  # segundos (valor inicial propuesto en ADR-003)
MODELO_POR_DEFECTO = "gemini-3.5-flash-lite"


@dataclass
class GeminiExito:
    """Respuesta generada por Gemini."""

    respuesta: str


@dataclass
class GeminiError:
    """Error o timeout de Gemini; el llamador informa 'IA no disponible'."""

    mensaje: str


ResultadoGemini = Union[GeminiExito, GeminiError]


class GeminiGateway:
    """Encapsula la llamada a Gemini con timeout y resultado tipado."""

    def __init__(
        self,
        timeout: float = TIMEOUT_POR_DEFECTO,
        modelo: Optional[str] = None,
        generador: Optional[Callable[[str], str]] = None,
    ):
        if timeout >= 30:
            raise ValueError("El timeout de GeminiGateway debe ser menor a 30 segundos")
        self.timeout = timeout
        self.modelo = modelo or os.getenv("GEMINI_MODEL", MODELO_POR_DEFECTO)
        # generador permite inyectar un doble de prueba; por defecto se usa la API real
        self._generador = generador or self._generar_con_api

    def _generar_con_api(self, prompt: str) -> str:
        """Llama a Gemini API usando la clave de la variable de entorno."""
        clave = os.getenv("GEMINI_API_KEY")
        if not clave:
            raise RuntimeError("Clave de API no configurada")

        from google import genai
        from google.genai import types

        cliente = genai.Client(
            api_key=clave,
            http_options=types.HttpOptions(timeout=int(self.timeout * 1000)),  # en milisegundos
        )
        respuesta = cliente.models.generate_content(model=self.modelo, contents=prompt)
        return respuesta.text

    def generar_respuesta(self, prompt: str) -> ResultadoGemini:
        """Genera una respuesta; nunca eleva excepciones al llamador."""
        ejecutor = ThreadPoolExecutor(max_workers=1)
        futuro = ejecutor.submit(self._generador, prompt)
        try:
            texto = futuro.result(timeout=self.timeout)
        except FuturoTimeoutError:
            logger.error("Gemini excedio el tiempo limite de %s s", self.timeout)
            return GeminiError(mensaje=f"Tiempo de espera agotado ({self.timeout} s)")
        except Exception as e:
            logger.error("Error de Gemini API: %s", e)
            return GeminiError(mensaje=str(e) or e.__class__.__name__)
        finally:
            # No se espera al hilo: si Gemini sigue colgado, la respuesta al usuario no se bloquea
            ejecutor.shutdown(wait=False)

        if not texto or not texto.strip():
            return GeminiError(mensaje="Respuesta vacia de Gemini")
        return GeminiExito(respuesta=texto.strip())


_gateway_por_defecto = GeminiGateway()


def obtener_gateway_gemini() -> GeminiGateway:
    """Dependencia FastAPI: retorna el gateway compartido (se reemplaza en las pruebas)."""
    return _gateway_por_defecto

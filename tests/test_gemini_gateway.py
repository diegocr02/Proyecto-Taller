# Historia: H-08, H-09
"""
Pruebas unitarias de GeminiGateway (ADR-003): exito, timeout y error, sin llamar a la API real.
"""

import time

import pytest

from app.shared.gemini_gateway import GeminiError, GeminiExito, GeminiGateway


def test_gateway_exito():
    gateway = GeminiGateway(generador=lambda prompt: "  Hay 3 juegos de pastillas.  ")
    resultado = gateway.generar_respuesta("pregunta")
    assert resultado == GeminiExito(respuesta="Hay 3 juegos de pastillas.")


def test_gateway_timeout_retorna_error_sin_propagar():
    def lento(prompt):
        time.sleep(2)
        return "tarde"

    gateway = GeminiGateway(timeout=0.2, generador=lento)
    inicio = time.monotonic()
    resultado = gateway.generar_respuesta("pregunta")
    assert isinstance(resultado, GeminiError)
    assert "Tiempo de espera" in resultado.mensaje
    assert time.monotonic() - inicio < 1.5


def test_gateway_error_de_api_retorna_error():
    def falla(prompt):
        raise ConnectionError("403 API key not valid")

    resultado = GeminiGateway(generador=falla).generar_respuesta("pregunta")
    assert resultado == GeminiError(mensaje="403 API key not valid")


def test_gateway_respuesta_vacia_es_error():
    assert isinstance(GeminiGateway(generador=lambda p: "   ").generar_respuesta("x"), GeminiError)


def test_gateway_sin_clave_retorna_error(monkeypatch):
    """La clave se lee solo de la variable de entorno; sin ella se degrada sin excepcion."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    resultado = GeminiGateway().generar_respuesta("pregunta")
    assert isinstance(resultado, GeminiError)


def test_gateway_rechaza_timeout_de_30_segundos_o_mas():
    with pytest.raises(ValueError):
        GeminiGateway(timeout=30)

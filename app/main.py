# Historia: H-08 (arranque y verificación de la clave), H-01..H-09 (registro de routers)
"""
Punto de entrada principal de la aplicacion FastAPI para Jorge Motors.
Configura el ciclo de vida, verifica credenciales segun Requisito 8.3,
monta archivos estaticos del frontend y registra los routers de los modulos.
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv

from app.modules.ordenes.router import router as router_ordenes
from app.modules.historial.router import router as router_historial
from app.modules.inventario.router import router as router_inventario
from app.modules.alertas.router import router as router_alertas
from app.modules.comparacion.router import router as router_comparacion
from app.modules.reportes.router import router as router_reportes
from app.modules.asistente.router import router as router_asistente
from data.seed import RUTA_BASE_DATOS_POR_DEFECTO, inicializar_base_datos, poblar_datos_simulados

# Cargar variables de entorno desde archivo .env si existe
load_dotenv()

# Configuracion de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("asistente_taller")


def verificar_clave_gemini() -> None:
    """
    Verifica la presencia de la clave GEMINI_API_KEY segun Requisito 8.3.
    Termina el proceso con codigo distinto de cero si no esta definida,
    a menos que se indique MODO_TEST=1 para entornos de pruebas aislados.
    """
    clave = os.getenv("GEMINI_API_KEY")
    modo_test = os.getenv("MODO_TEST", "0") == "1"

    if not clave and not modo_test:
        logger.error("Error de configuracion: clave de API de asistencia no configurada.")
        sys.exit(1)


def preparar_base_datos() -> None:
    """Crea las tablas que falten y, si la base no existia, la puebla con datos simulados."""
    existia = os.path.exists(RUTA_BASE_DATOS_POR_DEFECTO)
    inicializar_base_datos(RUTA_BASE_DATOS_POR_DEFECTO)
    if not existia:
        poblar_datos_simulados(RUTA_BASE_DATOS_POR_DEFECTO)
        logger.info("Base de datos simulada creada en %s", RUTA_BASE_DATOS_POR_DEFECTO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicacion FastAPI."""
    verificar_clave_gemini()
    preparar_base_datos()
    logger.info("Aplicacion iniciada exitosamente.")
    yield
    logger.info("Aplicacion detenida.")


app = FastAPI(
    title="Jorge Motors - Asistente de Gestion de Taller y Repuestos",
    description="Sistema digital para ordenes de trabajo, inventario y asistencia de taller",
    version="1.0.0",
    lifespan=lifespan,
)

def _describir_error(error: dict) -> str:
    """Traduce un error de validacion de Pydantic a un mensaje en espanol con el campo indicado."""
    partes = [str(p) for p in error.get("loc", ()) if p not in ("body", "query", "path")]
    campo = ".".join(partes) or "solicitud"
    tipo = error.get("type", "")
    ctx = error.get("ctx") or {}

    if tipo == "missing":
        return f"El campo '{campo}' es obligatorio"
    if tipo == "value_error":
        return str(ctx.get("error", error.get("msg", "")))
    if tipo == "string_too_short":
        return f"El campo '{campo}' no puede estar vacío"
    if tipo == "string_too_long":
        return f"El campo '{campo}' admite como máximo {ctx.get('max_length')} caracteres"
    if tipo == "greater_than_equal":
        return f"El campo '{campo}' debe ser mayor o igual a {ctx.get('ge')}"
    if tipo == "less_than_equal":
        return f"El campo '{campo}' debe ser menor o igual a {ctx.get('le')}"
    if tipo in ("int_parsing", "int_type", "int_from_float"):
        return f"El campo '{campo}' debe ser un número entero"
    if tipo.startswith("date"):
        return f"El campo '{campo}' debe ser una fecha válida (AAAA-MM-DD)"
    if tipo == "literal_error":
        return f"El campo '{campo}' debe ser uno de: {ctx.get('expected')}"
    return f"El campo '{campo}' no es válido"


@app.exception_handler(RequestValidationError)
async def manejar_error_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Responde 422 con un mensaje legible y la lista de campos con error (Requisito 1.4)."""
    errores = exc.errors()
    campos = [".".join(str(p) for p in e.get("loc", ()) if p not in ("body", "query", "path")) for e in errores]
    detalle = "; ".join(_describir_error(e) for e in errores)
    return JSONResponse(status_code=422, content={"detail": detalle, "campos": campos})


# Montar archivos estaticos si la carpeta existe
ruta_frontend = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
ruta_estaticos = os.path.join(ruta_frontend, "static")

if os.path.exists(ruta_estaticos):
    app.mount("/static", StaticFiles(directory=ruta_estaticos), name="static")


@app.get("/", include_in_schema=False)
def servir_inicio():
    """Sirve la pagina principal index.html."""
    ruta_index = os.path.join(ruta_frontend, "index.html")
    if os.path.exists(ruta_index):
        return FileResponse(ruta_index)
    return {"mensaje": "Jorge Motors API operativa"}


# Registrar routers
app.include_router(router_ordenes)
app.include_router(router_historial)
app.include_router(router_inventario)
app.include_router(router_alertas)
app.include_router(router_comparacion)
app.include_router(router_reportes)
app.include_router(router_asistente)

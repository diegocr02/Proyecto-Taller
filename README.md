# Asistente de Gestión de Taller y Repuestos · Jorge Motors

Aplicación web (FastAPI + HTML/JS + SQLite) para registrar Órdenes de Trabajo, consultar historial y stock, ver alertas de stock mínimo, comparar el conteo físico, generar reportes por técnico y consultar un asistente con IA (Gemini). Todos los datos son simulados (Ley N.° 29733).

La documentación del proyecto está en `.kiro/steering/`, `.kiro/specs/asistente-taller-jorge-motors/` y `docs/`.

## Puesta en marcha

```bash
python -m pip install -r requirements.txt
cp .env.example .env          # y colocar una GEMINI_API_KEY válida en .env
python data/seed.py           # opcional: la app crea data/taller.db al arrancar si no existe
python -m uvicorn app.main:app --port 8000
```

Abrir <http://localhost:8000> y elegir el rol en la esquina superior.

Si `GEMINI_API_KEY` no está definida, el proceso termina al arrancar (Requisito 8.3). Si la clave existe pero Gemini falla, solo el asistente responde "Asistencia de IA no disponible en este momento"; el resto del sistema sigue funcionando.

Variables opcionales: `GEMINI_MODEL` (por defecto `gemini-3.5-flash-lite`).

## Pruebas

```bash
python -m pytest
```

Incluye pruebas unitarias, las 17 propiedades PBT de `design.md` (Hypothesis, 100 ejemplos cada una) y la prueba de rendimiento de R7.1 (`docs/resultados_rendimiento.md`).

## Servidor MCP

Hasta la semana 4, `McpReadClient` (`app/shared/mcp_client.py`) usa un stub que lee `data/taller.db` en modo solo lectura. Al conectar el Servidor MCP real, solo cambia ese archivo.

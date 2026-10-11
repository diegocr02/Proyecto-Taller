# Asistente de Gestión de Taller y Repuestos · Jorge Motors

Aplicación web (FastAPI + HTML/JS + SQLite) para registrar Órdenes de Trabajo, consultar historial y stock, ver alertas de stock mínimo, comparar el conteo físico, generar reportes por técnico y consultar un asistente con IA (Gemini). Todos los datos son simulados (Ley N.° 29733).

La documentación del proyecto está en `.kiro/steering/`, `.kiro/specs/asistente-taller-jorge-motors/` y `docs/`.

## Puesta en marcha

Requisitos: Python 3.11 o superior y una clave propia de Gemini (gratis en <https://aistudio.google.com/apikey>). La clave nunca se sube al repositorio.

```bash
git clone https://github.com/diegocr02/Proyecto-Taller.git
cd Proyecto-Taller
git checkout develop
python -m pip install -r requirements.txt
cp .env.example .env          # y colocar una GEMINI_API_KEY válida en .env
python data/seed.py           # opcional: la app crea data/taller.db al arrancar si no existe
python -m uvicorn app.main:app --port 8000
```

Abrir <http://localhost:8000> y elegir el rol en la esquina superior.

Si `GEMINI_API_KEY` no está definida, el proceso termina al arrancar (Requisito 8.3). Si la clave existe pero Gemini falla, solo el asistente responde "Asistencia de IA no disponible en este momento"; el resto del sistema sigue funcionando.

Variables opcionales: `GEMINI_MODEL` (por defecto `gemini-3.5-flash-lite`).

En Windows (PowerShell), en lugar de `cp` use `copy .env.example .env` y edite `.env` con el Bloc de notas.

## Preguntas de ejemplo para el asistente IA

Elija el rol arriba a la derecha, abra la pantalla «Asistente IA» y pruebe:

| Rol | Pregunta |
|---|---|
| Encargado_Compras | ¿Qué repuestos tengo que comprar? |
| Técnico | ¿Cuántas pastillas de freno hay en stock? |
| Técnico | ¿Qué le hicieron al vehículo ABC-123? |
| Recepcionista | ¿Qué OT tiene el cliente con DNI 10000002? |
| Gerente | ¿En qué estado está el carro MNO-456 y quién lo atiende? |

El asistente solo responde con los datos del sistema (placas ABC-123, XYZ-789, MNO-456; DNI 10000001 a 10000003; repuestos REP-001 a REP-005). Si pregunta algo que no está en los datos, lo dice sin inventar.

## Entregables de la sesión 7

`docs/S7_Guia_de_laboratorio_LosPapus.docx` (guía completada), `docs/trazabilidad_s7.md`, `docs/registro_s7.md`, `docs/deuda_tecnica.md` y `docs/reto2_rompan_modulo_s7.md`.

## Pruebas

```bash
python -m pytest
```

Incluye pruebas unitarias, las 17 propiedades PBT de `design.md` (Hypothesis, 100 ejemplos cada una) y la prueba de rendimiento de R7.1 (`docs/resultados_rendimiento.md`).

## Servidor MCP

Hasta la semana 4, `McpReadClient` (`app/shared/mcp_client.py`) usa un stub que lee `data/taller.db` en modo solo lectura. Al conectar el Servidor MCP real, solo cambia ese archivo.

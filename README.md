# Asistente de Gestión de Taller y Repuestos · Jorge Motors

Aplicación web (FastAPI + HTML/JS + SQLite) para registrar Órdenes de Trabajo, consultar historial y stock, ver alertas de stock mínimo, comparar el conteo físico, generar reportes por técnico y conversar con **JorgeBot**, un agente de IA que consulta la base de datos mediante herramientas MCP. Todos los datos son simulados (Ley N.° 29733).

La documentación del proyecto está en `.kiro/steering/`, `.kiro/specs/asistente-taller-jorge-motors/` y `docs/`.

## Proyecto final: agente JorgeBot

| Entregable | Dónde está |
|---|---|
| Chat integrado en la aplicación | Pestaña «Asistente IA» (`frontend/`) |
| Servidor MCP con 7 herramientas | `agente/servidor_mcp.py` |
| Instrucciones del agente | `agente/instrucciones.txt` |
| Agente (ruta B, Python) | `agente/agente.py` |
| Puente chat → agente (equivale a `chat.php`) | `app/modules/asistente/router.py` |
| Ficha del agente | `docs/ficha_agente.md` |
| Tabla de 10 casos de prueba | `docs/casos_prueba.md` |
| Guion de la demostración | `docs/guion_demo.md` |

## Puesta en marcha

Requisitos: Python 3.10 o superior y una clave de IA. El agente usa la primera clave que encuentre en `.env`, en este orden: `OPENAI_API_KEY`, `GEMINI_API_KEY` (gratis en <https://aistudio.google.com/apikey>) o `GROQ_API_KEY` (contingencia). Las claves nunca se suben al repositorio (`.env` está en `.gitignore`).

```bash
git clone https://github.com/diegocr02/Proyecto-Taller.git
cd Proyecto-Taller
git checkout develop
python -m pip install -r requirements.txt      # incluye mcp[cli]<2 (la versión 2 no es compatible)
cp .env.example .env                           # y colocar una clave válida en .env
python data/seed.py                            # carga 20 registros simulados por tabla
python -m uvicorn app.main:app --port 8000     # sin --reload (en Windows impide encender el servidor MCP)
```

Abrir <http://localhost:8000>, elegir el rol en la esquina superior y entrar a «Asistente IA». En la terminal debe aparecer `Servidor MCP listo con 7 herramientas`: el agente enciende solo el servidor MCP, no hay que abrir otra terminal.

En Windows (PowerShell), en lugar de `cp` use `copy .env.example .env` y edite `.env` con el Bloc de notas.

Variables opcionales en `.env`: `OPENAI_MODEL` (por defecto `gpt-4o-mini`), `GEMINI_MODEL`, `GROQ_MODEL`, y `AGENTE_PROVEEDOR` (`openai`, `gemini` o `groq`) para elegir el modelo aunque haya varias claves.

Si no hay ninguna clave, el proceso termina al arrancar (Requisito 8.3). Si la clave existe pero la IA falla, solo el asistente responde "Asistencia de IA no disponible en este momento"; el resto del sistema sigue funcionando.

### Probar el servidor MCP solo

```bash
python agente/servidor_mcp.py      # queda esperando por stdio; se puede conectar desde VS Code como cliente MCP
python -m pytest tests/test_agente.py
```

## Preguntas de ejemplo para el asistente IA

| Pregunta | Herramienta MCP que usa |
|---|---|
| ¿Qué hay de stock? / Dame el inventario | `listar_inventario` |
| ¿Cuántas baterías quedan? | `buscar_repuesto` |
| ¿Qué repuestos debo reponer? | `repuestos_por_reponer` |
| ¿Qué trabajos tiene la placa ABC-123? | `historial_vehiculo` |
| ¿Qué órdenes tiene el DNI 10000002? | `historial_cliente` |
| ¿Qué órdenes tiene pendientes Luis Luna? | `ordenes_pendientes` |
| ¿Cuántas órdenes atendió cada técnico este mes? | `resumen_ordenes_por_tecnico` |

Recuerda la conversación ("¿Y cuál es su stock mínimo?"), rechaza temas ajenos al taller y no revela datos personales. Datos simulados: placas como ABC-123, XYZ-789, CDE-345; DNI 10000001 a 10000020; repuestos REP-001 a REP-020.

## Entregables de la sesión 7

`docs/S7_Guia_de_laboratorio_LosPapus.docx` (guía completada), `docs/trazabilidad_s7.md`, `docs/registro_s7.md`, `docs/deuda_tecnica.md` y `docs/reto2_rompan_modulo_s7.md`.

## Pruebas

```bash
python -m pytest
```

Incluye pruebas unitarias, las 17 propiedades PBT de `design.md` (Hypothesis, 100 ejemplos cada una) y la prueba de rendimiento de R7.1 (`docs/resultados_rendimiento.md`).

## Servidor MCP

El agente usa el servidor MCP real `agente/servidor_mcp.py` (7 herramientas, base en solo lectura). Las pantallas clásicas (inventario, historial, alertas) siguen usando `McpReadClient` (`app/shared/mcp_client.py`), que lee `data/taller.db` en modo solo lectura.

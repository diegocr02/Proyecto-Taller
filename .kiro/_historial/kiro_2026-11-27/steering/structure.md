---
inclusion: auto
name: structure
description: Estructura de carpetas canónica del proyecto asistente_taller. Activar cuando se discuta dónde crear, mover o nombrar archivos y directorios.
---

# Estructura de carpetas · Asistente de Gestión de Taller y Repuestos · Jorge Motors

> Fuente de verdad para la ubicación de todos los archivos del proyecto.
> Toda referencia en design.md, tasks.md o cualquier ADR debe coincidir con este documento.

> Actualizado por ingeniería inversa del repositorio el 2026-11-27 (`git ls-files`).

```
Proyecto-Taller/           ← raíz del repositorio
  app/
    main.py                ← entrada FastAPI: verifica la clave de IA, prepara la BD, enciende el
                             Servidor MCP del agente en segundo plano, monta routers y estáticos
    modules/
      ordenes/             ← Módulo OT (H1): schemas.py, router.py, repositorio.py
      historial/           ← Módulo Historial (H2): schemas.py, router.py
      inventario/          ← Módulo Inventario (H3): schemas.py, router.py
      alertas/             ← Módulo Alertas (H4): schemas.py, router.py
      comparacion/         ← Módulo Comparación (H5): schemas.py, router.py, repositorio.py
      reportes/            ← Módulo Reportes (H6): schemas.py, router.py
      asistente/           ← Módulo Asistente IA (H9): schemas.py, router.py, repositorio.py (trazabilidad)
    shared/
      mcp_client.py        ← McpReadClient: lectura de solo lectura para H2–H6 (stub sobre SQLite mode=ro)
      gemini_gateway.py    ← GeminiGateway: HEREDADO, sin uso en ejecución (solo su prueba)
  agente/                  ← Agente JorgeBot (proyecto final, H9)
    agente.py              ← AgenteTaller: bucle de herramientas, proveedores OpenAI/Gemini/Groq
    servidor_mcp.py        ← Servidor MCP (FastMCP, stdio): 7 herramientas de solo lectura
    instrucciones.txt      ← instrucciones (prompt de sistema) del agente
  frontend/
    index.html             ← SPA principal servida como archivo estático por FastAPI
    static/
      app.js               ← lógica JS: llamadas a la API REST, spinner, timeout 30 s, chat
      styles.css           ← estilos
      img/jorgebot.webp    ← avatar del agente
  data/
    taller.db              ← base de datos SQLite (generada por seed.py; nunca se versiona)
    seed.py                ← crea las 7 tablas y los datos simulados (sin datos personales reales)
    exportar_a_xampp.py    ← copia de solo revisión de taller.db a MySQL de XAMPP (base jorge_motors_app)
  tests/
    conftest.py            ← base temporal y dobles de prueba compartidos
    test_ordenes.py        ← pruebas unitarias y PBT del Módulo OT
    test_ordenes_detalle.py
    test_historial.py
    test_inventario.py
    test_alertas.py
    test_comparacion.py
    test_reportes.py
    test_asistente.py
    test_agente.py         ← Servidor MCP (7 herramientas) y ciclo del agente
    test_mcp_client.py
    test_gemini_gateway.py
    test_rendimiento.py    ← p95 ≤ 5 s (R7.1)
  docs/
    ADR-001.md             ← FastAPI vs Flask vs Django
    ADR-002.md             ← Acceso a datos: lecturas MCP, escrituras repositorio propio
    ADR-003.md             ← Integración de IA con degradación controlada
    ficha_agente.md, casos_prueba.md, guion_demo.md   ← proyecto final (agente)
    deuda_tecnica.md, resultados_rendimiento.md
    registro_s7.md, trazabilidad_s7.md, reto2_rompan_modulo_s7.md, S7_Guia_de_laboratorio_LosPapus.docx
    maquetas/wireframe_jorge_motors.html
  .env.example             ← plantilla: GEMINI_API_KEY, OPENAI_API_KEY, GROQ_API_KEY, *_MODEL, AGENTE_PROVEEDOR
  .gitignore               ← incluye .env, data/taller.db*, __pycache__, .pytest_cache, .hypothesis
  pytest.ini
  requirements.txt         ← fastapi, uvicorn, httpx, python-dotenv, google-genai, pytest,
                             hypothesis, pydantic, mcp[cli]<2
  README.md
```

## Reglas de nomenclatura

- Módulos de dominio: `app/modules/<nombre_en_minúscula_sin_tildes>/`
- Archivos dentro de cada módulo: siempre `schemas.py`, `router.py` y, si hay escrituras, `repositorio.py`
- Archivos compartidos: solo en `app/shared/`; no crear subcarpetas en shared/
- Tests: un archivo por módulo, con prefijo `test_`
- La base de datos `data/taller.db` nunca se incluye en el repositorio si contiene datos; solo se versiona `seed.py`

## Puertos por proceso (confirmado el 2026-11-27)

| Proceso | Puerto |
|---|---|
| FastAPI App (`python -m uvicorn app.main:app --port 8000`) | 8000 |
| Servidor MCP (`agente/servidor_mcp.py`) | Ninguno: es un proceso hijo que habla por stdio con el agente |
| MySQL de XAMPP (solo para la copia opcional `jorge_motors_app`) | 3306; la app no lo usa |

---

## Historial de cambios

| Fecha | Hallazgo que lo origina | Cambio realizado |
|---|---|---|
| 2026-09-25 | Auditoría Fase 1: estructura de carpetas documentada solo en design.md y tasks.md, sin archivo de steering canónico | Archivo creado como steering con inclusion: auto |
| 2026-11-27 | Ingeniería inversa del repositorio: faltaban `agente/`, `data/exportar_a_xampp.py`, varios tests y docs; el puerto 8001 del MCP no existe | Árbol actualizado a los archivos reales; puertos confirmados (el MCP usa stdio, no un puerto) |

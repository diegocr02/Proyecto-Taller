# Registro de la sesión 7 · Equipo <n.º>

Respuesta a la pregunta de la sección 2: para que en la semana 11 el agente consulte los datos del taller, hoy tienen que existir la base `data/taller.db` con datos simulados y endpoints de solo lectura (`McpReadClient` + `/historial`, `/inventario`, `/alertas`, `/reportes`) que devuelvan esos datos en JSON y respondan 404/503 de forma predecible.

Créditos de Kiro al inicio: <n> · Herramienta principal: Claude Code (Kiro se usó en S5–S6 para la spec)

> Adaptación declarada: la guía pide Laravel sobre XAMPP; el proyecto usa FastAPI + SQLite según `docs/ADR-001.md`. Pendiente de confirmar con la docente.

| N.º | Hora | Herramienta | Tarea (H-xx) | Prompt (resumen o ID: PL-1, PL-2…) | Resultado | Decisión (aceptado / corregido / rechazado) | Archivos leídos (lector) |
|-----|------|-------------|--------------|-------------------------------------|-----------|---------------------------------------------|--------------------------|
| 1 | 2026-10-10 | Claude Code | — | «Revisa la guía 7 y ve si ya completamos todo» | Lista de lo hecho y lo faltante frente a la guía | Aceptado | Ninguno modificado |
| 2 | 2026-10-10 | Claude Code | H-01…H-09 | «Haz todos los pasos de la guía y completa» (equivale a PL-1 + PL-2 + PL-4) | IDs H-xx en `requirements.md`; reglas S7 en `tech.md`; `tasks.md` podado (3 eliminadas, 3 divididas); `docs/trazabilidad_s7.md`; comentario `# Historia` en cada archivo; `GET /ordenes/{id}` responde 404 ante cualquier id no numérico; prueba `tests/test_ordenes_detalle.py` (7 casos en verde); 69/69 pruebas en verde | <aceptado / corregido> | `app/modules/ordenes/router.py` (<nombre>) · `tests/test_ordenes_detalle.py` (<nombre>) · `tasks.md` (<nombre>) · `docs/trazabilidad_s7.md` (<nombre>) |
| 3 |  |  |  |  |  |  |  |

Total de solicitudes usadas: 2 de 10
Hallazgos recibidos: <n> · corregidos: <n> · refutados: <n>
Herramienta final: Claude Code · ¿Cambió? <sí/no y por qué>

## Lista de cotejo 6.5 aplicada a la rebanada `GET /ordenes/{id_ot}` [H-01]

| # | Pregunta | Resultado |
|---|---|---|
| 1 | ¿Corre? | `/ordenes/1` → 200 con «Mantenimiento preventivo 45k» |
| 2 | ¿Traza? | `router.py`, `repositorio.py`, `schemas.py` y la prueba empiezan con `# Historia: H-01` |
| 3 | ¿Valida? | id solo numérico de hasta 9 dígitos; `/ordenes/no-existe-zz` → 404 |
| 4 | ¿Parametriza? | `WHERE ot.id = ?` con parámetro; sin SQL concatenado |
| 5 | ¿Protege? | Clave Gemini solo en `.env`, que está en `.gitignore` |
| 6 | ¿Respeta el diseño? | Módulo `ordenes/` con router + repositorio + schemas, igual que `design.md` |

## Reto de curiosidad

Pregunta: ¿por qué se consulta la base con `sqlite3` y SQL parametrizado y no con un ORM?
Respuesta del agente: ADR-002 decide que las lecturas van por el Servidor_MCP de solo lectura y las escrituras por un repositorio propio en cada módulo, usando el `sqlite3` que ya trae Python; tech.md pide además evitar capas innecesarias, por eso no se añadió un ORM. El `?` evita la inyección SQL. Ojo: `GET /ordenes/{id}` lee con `RepositorioOT` y no por el MCP, lo que se aparta de ADR-002 (ver `docs/deuda_tecnica.md`).
¿Coincide con `design.md`? <completar tras leer design.md>

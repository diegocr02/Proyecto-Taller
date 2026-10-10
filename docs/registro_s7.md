# Registro de la sesión 7 · Equipo Los papus

Respuesta a la pregunta de la sección 2: para que en la semana 11 el agente consulte los datos del taller, hoy tienen que existir la base `data/taller.db` con datos simulados y endpoints de solo lectura (`McpReadClient` + `/historial`, `/inventario`, `/alertas`, `/reportes`) que devuelvan esos datos en JSON y respondan 404/503 de forma predecible.

Créditos de Kiro al inicio: no se usó Kiro en esta sesión (0 solicitudes de Kiro) · Herramienta principal: Claude Code

**Uso de Kiro en el proyecto:** la spec completa se generó con Kiro en S5–S6: `requirements.md`, `design.md` y el `tasks.md` original (fase Tasks del panel Specs). En esta sesión `tasks.md` no se regeneró: se podó y se trazó sobre esa versión de Kiro.

**Por qué se cambió a Claude Code en S7:** decisión del equipo; Claude Code ya tenía cargado el proyecto completo (código, pruebas y spec) y permitió avanzar en esta sesión sin reconstruir el contexto en otra herramienta. Si más adelante se ejecuta algún prompt en Kiro, se registrará en una fila nueva (posible reto 3 · cambio de herramienta).

> Adaptación declarada: la guía pide Laravel sobre XAMPP; el proyecto usa FastAPI + SQLite según `docs/ADR-001.md`. Pendiente de confirmar con la docente.

| N.º | Hora | Herramienta | Tarea (H-xx) | Prompt (resumen o ID: PL-1, PL-2…) | Resultado | Decisión (aceptado / corregido / rechazado) | Archivos leídos (lector) |
|-----|------|-------------|--------------|-------------------------------------|-----------|---------------------------------------------|--------------------------|
| 1 | 2026-10-10 | Claude Code | — | «Revisa la guía 7 y ve si ya completamos todo» | Lista de lo hecho y lo faltante frente a la guía | Aceptado | Ninguno modificado |
| 2 | 2026-10-10 | Claude Code | H-01…H-09 | «Haz todos los pasos de la guía y completa» (equivale a PL-1 + PL-2 + PL-4) | IDs H-xx en `requirements.md`; reglas S7 en `tech.md`; `tasks.md` podado (3 eliminadas, 3 divididas); `docs/trazabilidad_s7.md`; comentario `# Historia` en cada archivo; `GET /ordenes/{id}` responde 404 ante cualquier id no numérico; prueba `tests/test_ordenes_detalle.py` (7 casos en verde); 69/69 pruebas en verde | Aceptado | `app/modules/ordenes/router.py` (Los papus) · `tests/test_ordenes_detalle.py` (Los papus) · `tasks.md` (Los papus) · `docs/trazabilidad_s7.md` (Los papus) |
| 3 | 2026-10-10 | Claude Code | H-01, S7 | «Este es el link del repositorio; autor Los papus» | Rama `develop` creada sobre `main` del equipo; 5 commits con formato `tipo(H-xx)`; push a GitHub; `.env` y `taller.db` fuera del repositorio | Aceptado | Mensajes de commit y `git status` (Los papus) |
| 4 | 2026-10-10 | Claude Code | S7 | «Edita el registro y complétalo» | Registro completado y respuesta del reto de curiosidad contrastada con `design.md` | Aceptado | `docs/registro_s7.md` (Los papus) |

Total de solicitudes usadas: 4 de 10
Hallazgos recibidos: 0 · corregidos: 0 · refutados: 0 (a la fecha de este registro)
Hallazgos propios corregidos: 1 — `GET /ordenes/{id}` respondía 422 con ids no numéricos; corregido en el commit `fix(H-01)` (ver `docs/reto2_rompan_modulo_s7.md`)
Herramienta final: Claude Code · ¿Cambió? No. Se mantuvo la misma herramienta en toda la sesión porque ya tenía el contexto del proyecto completo.

## Lista de cotejo 6.5 aplicada a la rebanada `GET /ordenes/{id_ot}` [H-01]

| # | Pregunta | Resultado |
|---|---|---|
| 1 | ¿Corre? | `/ordenes/1` → 200 con «Mantenimiento preventivo 45k» |
| 2 | ¿Traza? | `router.py`, `repositorio.py`, `schemas.py` y la prueba empiezan con `# Historia: H-01` |
| 3 | ¿Valida? | id solo numérico de hasta 9 dígitos; `/ordenes/no-existe-zz` → 404 |
| 4 | ¿Parametriza? | `WHERE ot.id = ?` con parámetro; sin SQL concatenado |
| 5 | ¿Protege? | Clave Gemini solo en `.env`, que está en `.gitignore` y no aparece en GitHub |
| 6 | ¿Respeta el diseño? | Parcialmente: la estructura `ordenes/` (router + repositorio + schemas) coincide con `design.md`, pero la lectura usa `RepositorioOT` (ver reto de curiosidad) |

## Reto de curiosidad

Pregunta: ¿por qué se consulta la base con `sqlite3` y SQL parametrizado y no con un ORM?
Respuesta del agente: ADR-002 decide que las lecturas van por el Servidor_MCP de solo lectura y las escrituras por un repositorio propio en cada módulo, usando el `sqlite3` que ya trae Python; tech.md pide además evitar capas innecesarias, por eso no se añadió un ORM. El `?` evita la inyección SQL. Ojo: `GET /ordenes/{id}` lee con `RepositorioOT` y no por el MCP, lo que se aparta de ADR-002 (ver `docs/deuda_tecnica.md`).
¿Coincide con `design.md`? En parte. `design.md` (línea 7) dice que «las lecturas de inventario e historial se canalizan a través de un servidor MCP» y que las escrituras van por repositorios; la tabla de componentes (línea 215) define `RepositorioOT` solo para «INSERT/UPDATE». El uso de SQLite parametrizado sin ORM coincide; que `RepositorioOT` también haga la lectura de `GET /ordenes/{id}` no coincide. Queda registrado como deuda técnica y es candidato al reto 1 («Atrapa al agente»).

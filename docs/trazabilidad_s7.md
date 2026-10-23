# Trazabilidad de tareas · Sesión 7

Proyecto: Asistente de Gestión de Taller y Repuestos — Jorge Motors
Fuente: `.kiro/specs/asistente-taller-jorge-motors/tasks.md` (podado el 2026-10-10)
Historias: `requirements.md`, Requisito N = H-0N.

> Adaptación: la guía S7 pide Laravel sobre XAMPP. Este proyecto usa FastAPI + SQLite según ADR-001, por eso las URL se sirven con `python -m uvicorn app.main:app --port 8000` y las «vistas» son las pantallas de `frontend/`.

| N.º tarea | Título corto | Historia (H-xx) | Decisión | Justificación | Verificación (URL y resultado esperado) |
|---|---|---|---|---|---|
| 0 | Detalle de una OT (rebanada vertical prioritaria) | H-01 | MANTENER (primera) | Sin OT registrada y consultable el resto del sistema no sirve; las tablas `ordenes_trabajo`, `clientes` y `vehiculos` ya tienen datos | `/ordenes/1` → 200 con «Mantenimiento preventivo 45k»; `/ordenes/no-existe-zz` → 404 |
| 1 | Estructura del proyecto y base de datos | — | ELIMINAR · ya realizada | Crear el proyecto, `.env.example` y la base de datos ya se hizo en S5–S6 | — |
| 2 | Registro de OT (schema, repositorio, router) | H-01 | MANTENER | Vertical: atraviesa schema, repositorio SQLite, router y pantalla de registro | `POST /ordenes` con los 9 campos → 201 con `id_ot`; sin un campo → 422 indicando el campo |
| 3 | Punto de control módulo OT | — | ELIMINAR · no es construcción | No traza a ninguna historia; lo cubren las pruebas de la tarea 2 | — |
| 4 | McpReadClient | H-02…H-06 | DIVIDIR | Horizontal: un cliente para cinco historias; cada método se construye dentro de su rebanada (5, 6, 7, 8, 10) | Se verifica en cada rebanada |
| 5 | Historial por placa o DNI | H-02 | MANTENER | Vertical: router → McpReadClient → SQLite → pantalla Historial | `/historial?q=ABC-123` → 200 con 1 OT; `/historial/9999` → 404; `/historial?q=@@` → 422 |
| 6 | Consulta de stock | H-03 | MANTENER | Vertical, solo lectura | `/inventario?q=REP-001` → 200 con «Pastillas de freno delanteras»; `/inventario?q=zzz` → 200 con «Repuesto no encontrado» |
| 7 | Alertas de stock mínimo | H-04 | MANTENER | Vertical; los datos simulados ya tienen 3 repuestos en alerta | `/alertas` → 200 con REP-001, REP-003 y REP-005 |
| 8 | Comparación de conteo físico | H-05 | MANTENER | Vertical: schema → router → MCP → repositorio → pantalla | `POST /comparacion` con `REP-001` = 5 → diferencia +2 y descuadre marcado |
| 9 | Punto de control módulos de dominio | — | ELIMINAR · no es construcción | No traza a ninguna historia | — |
| 10 | Reporte por técnico + CSV | H-06 | MANTENER | Vertical; incluye exportación CSV | `/reportes?fecha_inicio=2026-01-01&fecha_fin=2026-12-31` → 200 por técnico; inicio > fin → 422 |
| 11 | GeminiGateway y Asistente IA | H-08, H-09 | DIVIDIR | Son dos piezas: 11.1 gateway (H-08, clave en variable de entorno) y 11.3 router Asistente con trazabilidad (H-09) | `POST /asistente` → 200; si Gemini falla → «Asistencia de IA no disponible» y registro en `trazabilidad_ia` |
| 12 | Indicador de carga y timeouts | H-07 | MANTENER | Acotada y verificable en el navegador | Petición > 2 s muestra spinner; > 30 s muestra error con «Reintentar» |
| 13 | Frontend completo | H-01…H-09 | DIVIDIR | Horizontal («todas las pantallas»); cada pantalla va con su rebanada | `http://127.0.0.1:8000/` muestra el selector de rol y las pantallas |
| 14 | Punto de control final + smoke test p95 | H-07 | MANTENER solo 14.1 | El smoke test sí verifica H-07.1; el punto de control se elimina | `pytest tests/test_rendimiento.py` en verde; resultado en `docs/resultados_rendimiento.md` |

**Resumen de la poda:** 15 tareas revisadas · 9 mantenidas (todas con historia) · 3 eliminadas · 3 divididas.

**Hallazgo de la poda:** ninguna tarea faltaba en `requirements.md`, pero las historias no tenían identificador; se añadieron `[H-01]`…`[H-09]` a los encabezados de los requisitos.

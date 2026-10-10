# Resultados de rendimiento · R7.1 (tarea 14.1)

**Criterio:** al menos el 95 % de las consultas de historial y de stock responden en 5 s o menos (p95 ≤ 5 s), con un único usuario concurrente.

## Condiciones de la medición

| Parámetro | Valor |
|---|---|
| Fecha | 2026-10-09 |
| Equipo | Windows 11 (10.0.26200), Python 3.12.10 |
| Servidor | `python -m uvicorn app.main:app --port 8765` (un proceso) |
| Cliente | `httpx` contra `http://localhost:8765`, 100 peticiones consecutivas por endpoint |
| Datos | `data/taller.db` generada por `data/seed.py` (datos simulados) |
| Servidor MCP | **Stub de `McpReadClient` sobre SQLite en solo lectura.** El Servidor MCP real (semana 4) aún no está conectado |

## Resultados

| Endpoint | Consulta | p50 | p95 | Máximo | ¿Cumple p95 ≤ 5 s? |
|---|---|---|---|---|---|
| `GET /historial` | `q=ABC-123` | 2,8 ms | 7,5 ms | 2 075,5 ms | Sí |
| `GET /inventario` | `q=aceite` | 1,8 ms | 4,1 ms | 21,7 ms | Sí |

El máximo de `/historial` corresponde a la primera petición (resolución de `localhost` y conexión inicial en Windows); no afecta al p95.

## Prueba automatizada

`tests/test_rendimiento.py` repite la medición (100 peticiones por endpoint con `TestClient`) en cada ejecución de `pytest` y falla si el p95 supera 5 s.

## Pendiente

Repetir la medición cuando el Servidor MCP real de la semana 4 esté conectado, ya que añadirá la latencia del protocolo MCP. Si el p95 supera 5 s, abrir una incidencia en el repositorio.

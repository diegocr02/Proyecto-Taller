# Deuda técnica

| Fecha | Historia | Deuda | Por qué importa | Qué haríamos |
|---|---|---|---|---|
| 2026-10-10 | H-01 | `GET /ordenes/{id}` lee con `RepositorioOT` y no a través del Servidor_MCP, a diferencia de ADR-002 (lecturas por MCP, escrituras por repositorio) | Dos caminos de lectura para los mismos datos; si cambia el esquema hay que tocar ambos | Mover la lectura a `McpReadClient.obtener_ot` (que ya existe para `/historial/{id}`) o justificar la excepción en ADR-002 |
| 2026-10-10 | H-01, H-02 | `/ordenes/{id}` y `/historial/{id}` devuelven casi lo mismo con dos esquemas distintos (`OTDetalle` y `OTHistorial`) | Duplicación: un cambio de campos se hace dos veces | Decidir en equipo si se conserva un solo endpoint de detalle |
| 2026-10-10 | Todas | El rol se elige en la pantalla sin autenticación (aceptado en ADR-002) | Cualquiera puede actuar como Gerente | Añadir inicio de sesión en la Unidad 3 si el alcance lo permite |
| 2026-10-10 | H-02…H-06 | `McpReadClient` usa un stub sobre SQLite; el Servidor_MCP real aún no está conectado | Las pruebas de caída del MCP son simuladas | Conectar el MCP real y repetir `tests/test_mcp_client.py` |

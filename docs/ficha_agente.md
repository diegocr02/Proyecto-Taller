# Ficha del agente — JorgeBot

**Proyecto:** Sistema de Gestión de Taller y Repuestos · Jorge Motors
**Equipo:** Los Papus · **Ruta elegida:** B (Python)
**Versión de la ficha:** 2.0 (2026-11-27), actualizada por ingeniería inversa de `agente/` y `app/modules/asistente/`.

| Campo | Contenido |
|---|---|
| **Nombre del agente** | JorgeBot |
| **Usuario** | Personal del taller Jorge Motors: recepcionista, técnicos, encargado de compras y gerente. Todos los roles ven la pestaña «Asistente IA». |
| **Preguntas que resuelve** | 0. ¿Qué hay de stock? (inventario completo)<br>1. ¿Cuánto stock queda de un repuesto y hay que reponerlo?<br>2. ¿Qué repuestos debo comprar o reponer?<br>3. ¿Qué trabajos se le hicieron a una placa? / ¿Qué órdenes tiene un DNI?<br>4. ¿Qué órdenes de trabajo están pendientes (en general o de un técnico)? / ¿Qué carros están en el taller?<br>5. ¿Cuántas órdenes atendió cada técnico en un periodo? |
| **Herramienta MCP por pregunta** | 0 → `listar_inventario` · 1 → `buscar_repuesto` · 2 → `repuestos_por_reponer` · 3 → `historial_vehiculo` y `historial_cliente` · 4 → `ordenes_pendientes` · 5 → `resumen_ordenes_por_tecnico` |
| **Datos que necesita** | Tablas `repuestos`, `stock`, `vehiculos`, `clientes` y `ordenes_trabajo` de `data/taller.db` (20 clientes, 20 vehículos, 20 repuestos y 23 OT simulados). |
| **Lo que no hace** | No registra, modifica ni elimina órdenes, repuestos ni clientes (la base se abre en solo lectura). No muestra nombres ni DNI de clientes. No responde temas ajenos al taller (deportes, clima, recetas, política). No inventa cifras. No consulta `trazabilidad_ia` ni `comparaciones_conteo`. |
| **Tono** | Breve, amable y claro, en español: una frase de resumen y una lista con guiones, en texto plano y con fechas en día/mes/año. Se presenta como asistente de inteligencia artificial al saludar. |
| **Acción de escritura** | Ninguna (decisión del equipo: el agente solo consulta). |
| **Modelo** | Intercambiable (ADR-005): OpenAI `gpt-4o-mini`, Gemini `gemini-2.5-flash` o Groq `llama-3.3-70b-versatile`. Se usa `AGENTE_PROVEEDOR` o, si no está definido, la primera clave en el orden OpenAI → Gemini → Groq. **Con el `.env` actual se usa OpenAI.** En las pruebas del equipo, `gpt-4o-mini` respondió en ~1–3 s (dato de la versión 1 de esta ficha; NO VERIFICADO en esta revisión). |

## Herramientas (Servidor MCP `agente/servidor_mcp.py`)

| Herramienta | Parámetros | Devuelve | Límite de filas |
|---|---|---|---|
| `buscar_repuesto` | `texto` | Repuestos que coinciden (sin tildes y sin plurales) con `requiere_reposicion` | 10 |
| `listar_inventario` | `solo_disponibles` (por defecto `false`) | Todo el inventario con `estado` (agotado / bajo el mínimo / en el mínimo / disponible) | 50 |
| `repuestos_por_reponer` | — | Repuestos con cantidad ≤ mínimo, del más crítico al menos crítico | 20 |
| `historial_vehiculo` | `placa` (acepta `ABC123`) | Vehículo y sus OT, de la más reciente a la más antigua | 10 OT |
| `historial_cliente` | `dni` (8 dígitos) | Vehículos y OT del DNI, **sin el nombre** | 10 OT |
| `ordenes_pendientes` | `tecnico` (opcional, sin tildes) | OT abiertas o en proceso | 20 |
| `resumen_ordenes_por_tecnico` | `fecha_inicio`, `fecha_fin` (AAAA-MM-DD) | Total y desglose por estado de cada técnico | 20 técnicos |

Las consultas SQL exactas están en `.kiro/specs/asistente-taller-jorge-motors/design.md`, sección «Herramientas del Servidor MCP».

## Límites (ADR-006)

| Límite | Valor |
|---|---|
| Tiempo máximo por llamada al modelo | 20 s |
| Tiempo máximo total por pregunta | 25 s; si se supera, el chat muestra «Asistencia de IA no disponible en este momento» |
| Rondas de herramientas por pregunta | 4 (en la 5.ª llamada el modelo ya no tiene herramientas y tiene que responder) |
| Espera por herramienta | 10 s (o lo que quede de los 25 s); si falla, el modelo recibe «La herramienta no respondió» |
| Espera al encender el servidor MCP | 15 s |
| Memoria por conversación | Últimos 10 mensajes (5 preguntas y respuestas); se pierde al reiniciar el servidor |
| Conversaciones en memoria a la vez | 200 |
| Largo de la pregunta | 1 a 500 caracteres; una pregunta de solo espacios se rechaza |
| Largo de la respuesta | `max_tokens` 450; `temperature` 0.2 |
| Conversaciones guardadas en el navegador | 15 |
| Corte del navegador | 30 s; el agente siempre termina antes, porque tiene un tope de 25 s |

## Cómo funciona

```
Chat (pestaña Asistente IA)
   │  POST /asistente  {pregunta, rol, sesion}
   ▼
app/modules/asistente/router.py   ← hace de chat.php: puente, valida y guarda la trazabilidad
   ▼
agente/agente.py                  ← el agente: instrucciones + memoria + modelo que decide la herramienta
   │  stdio (MCP)
   ▼
agente/servidor_mcp.py            ← 7 herramientas @mcp.tool(), solo SELECT, base en modo solo lectura
   ▼
data/taller.db (SQLite)
```

1. El usuario escribe en el chat de la aplicación.
2. El backend recibe el mensaje y se lo pasa al agente junto con el número de conversación.
3. El agente envía al modelo las instrucciones (`agente/instrucciones.txt`), la fecha de hoy, el rol, la conversación previa y la lista de herramientas MCP.
4. El modelo decide qué herramienta necesita; el agente la ejecuta en el servidor MCP.
5. El servidor MCP consulta la base de datos y devuelve el dato.
6. El modelo redacta la respuesta y el chat la muestra junto con la herramienta usada.
7. Cada consulta queda en `trazabilidad_ia`, con las herramientas usadas y sus argumentos.

## Seguridad y uso responsable

- Claves solo en `.env` (en `.gitignore`).
- Herramientas de solo lectura: la base se abre con `mode=ro`; todas las consultas usan parámetros `?` y `LIMIT`.
- Solo datos simulados (Ley N.° 29733); el agente no devuelve nombres ni DNI de clientes.
- Se presenta como inteligencia artificial en su primer mensaje (Ley N.° 31814).
- Cada consulta queda registrada en la tabla `trazabilidad_ia` con las herramientas que usó.
- Las preguntas y los resultados de las herramientas se envían al proveedor de IA externo; por eso solo se usan datos simulados.

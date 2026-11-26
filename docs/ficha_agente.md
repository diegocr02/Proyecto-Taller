# Ficha del agente — JorgeBot

**Proyecto:** Sistema de Gestión de Taller y Repuestos · Jorge Motors
**Equipo:** Los Papus · **Ruta elegida:** B (Python)

| Campo | Contenido |
|---|---|
| **Nombre del agente** | JorgeBot |
| **Usuario** | Personal del taller Jorge Motors: recepcionista, técnicos, encargado de compras y gerente. |
| **Preguntas que resuelve** | 1. ¿Cuánto stock queda de un repuesto y hay que reponerlo?<br>2. ¿Qué repuestos debo comprar o reponer?<br>3. ¿Qué trabajos se le hicieron a una placa? / ¿Qué órdenes tiene un DNI?<br>4. ¿Qué órdenes de trabajo están pendientes (en general o de un técnico)?<br>5. ¿Cuántas órdenes atendió cada técnico en un periodo? |
| **Herramienta MCP por pregunta** | 1 → `buscar_repuesto` · 2 → `repuestos_por_reponer` · 3 → `historial_vehiculo` y `historial_cliente` · 4 → `ordenes_pendientes` · 5 → `resumen_ordenes_por_tecnico` |
| **Datos que necesita** | Tablas `repuestos`, `stock`, `vehiculos`, `clientes` y `ordenes_trabajo` de `data/taller.db` (20 registros simulados por tabla). |
| **Lo que no hace** | No registra, modifica ni elimina órdenes, repuestos ni clientes (la base se abre en solo lectura). No muestra nombres ni DNI de clientes. No responde temas ajenos al taller (deportes, clima, recetas, política). No inventa cifras. |
| **Tono** | Breve, amable y claro, en español, con fechas en formato día/mes/año y listas con guiones. Se presenta como asistente de inteligencia artificial al saludar. |
| **Acción de escritura** | Ninguna (decisión del equipo: el agente solo consulta). |
| **Modelo** | OpenAI `gpt-4o-mini` (el más rápido en nuestras pruebas, ~1-3 s). Contingencia: Gemini o Groq, cambiando la clave en `.env`. |

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
agente/servidor_mcp.py            ← 6 herramientas @mcp.tool(), solo SELECT, base en modo solo lectura
   ▼
data/taller.db (SQLite)
```

1. El usuario escribe en el chat de la aplicación.
2. El backend recibe el mensaje y se lo pasa al agente junto con el número de conversación.
3. El agente envía al modelo las instrucciones (`agente/instrucciones.txt`), la conversación previa y la lista de herramientas MCP.
4. El modelo decide qué herramienta necesita; el agente la ejecuta en el servidor MCP.
5. El servidor MCP consulta la base de datos y devuelve el dato.
6. El modelo redacta la respuesta y el chat la muestra junto con la herramienta usada.

## Seguridad y uso responsable

- Claves solo en `.env` (en `.gitignore`); ninguna clave en el historial de GitHub.
- Herramientas de solo lectura: la base se abre con `mode=ro`, todas las consultas usan parámetros `?` y `LIMIT`.
- Solo datos simulados (Ley N.° 29733); el agente no devuelve nombres ni DNI de clientes.
- Se presenta como inteligencia artificial en su primer mensaje (Ley N.° 31814).
- Cada consulta queda registrada en la tabla `trazabilidad_ia` con las herramientas que usó.

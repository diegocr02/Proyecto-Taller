# Tecnología · Sistema de Gestión de Inventario Jorge Motors

Redacta en español.

## Backend
- Python 3.11+
- FastAPI

## Frontend
- HTML + JS simple (sin frameworks pesados)

## IA
- Agente JorgeBot (`agente/agente.py`) con herramientas MCP. Llama al modelo con la API compatible con OpenAI de uno de estos proveedores: OpenAI (`gpt-4o-mini`), Gemini (`gemini-2.5-flash`, gratis y el del instructivo) o Groq (`llama-3.3-70b-versatile`, contingencia)
- Se usa el primer proveedor con clave en `.env` (OpenAI → Gemini → Groq), o el que indique `AGENTE_PROVEEDOR`. Cada llamada al modelo tiene un límite de 20 s
- Las claves se guardan en variables de entorno, nunca en el código

## Base de datos
- SQLite (`data/taller.db`, modo WAL) con 7 tablas y datos simulados: clientes, vehiculos, ordenes_trabajo, repuestos, stock, trazabilidad_ia y comparaciones_conteo
- La app no usa MySQL ni XAMPP. `data/exportar_a_xampp.py` hace una copia opcional de solo revisión en MySQL de XAMPP (base `jorge_motors_app`)

## Integración de datos
- Servidor MCP propio y de solo lectura (`agente/servidor_mcp.py`, SDK `mcp[cli]<2`, transporte stdio) con 7 herramientas: consultar stock, listar inventario, repuestos por reponer, historial por placa y por DNI, órdenes pendientes y resumen por técnico. Lo usa el agente
- Los módulos H2–H6 leen con `McpReadClient` (SQLite `mode=ro`). Ninguna lectura modifica el inventario

## Control de versiones
- Git/GitHub

## Principio de diseño
- Sin sobreingeniería: priorizar la solución más simple que cumpla el alcance DENTRO definido, evitando patrones o capas innecesarias para un proyecto de un semestre.

## Reglas de la sesión 7
- Adaptación de la guía S7: el proyecto usa FastAPI + SQLite (ADR-001), no Laravel/XAMPP. La aplicación vive en `app/` y el frontend en `frontend/`; toda ruta de archivo es relativa a la raíz del repositorio.
- La base de datos `data/taller.db` YA EXISTE con tablas y datos simulados (`data/seed.py`). PROHIBIDO crear tablas nuevas, migraciones o seeders adicionales.
- Acceso a datos con `sqlite3` y consultas parametrizadas (`?`). Nunca SQL concatenado ni f-strings con datos del usuario.
- Todo parámetro de ruta se valida; si el recurso no existe o el parámetro no tiene el formato esperado, responder 404 (nunca 500).
- Cada archivo empieza con el comentario `# Historia: H-xx` (`// Historia: H-xx` en JS, `<!-- Historia: H-xx -->` en HTML).
- Mensajes de commit: `tipo(H-xx): descripción`. Rama de trabajo: `develop`.
- `.env` nunca se versiona; las claves de IA solo viven en variables de entorno.

## Historial de cambios

| Fecha | Hallazgo que lo origina | Cambio realizado |
|---|---|---|
| 2026-11-27 | Ingeniería inversa: IA descrita como «solo Gemini»; el MCP incluía «actualizar inventario», que no existe (el MCP es de solo lectura) | Secciones IA, Base de datos e Integración de datos actualizadas al agente JorgeBot, los 3 proveedores, las 7 tablas y las 7 herramientas MCP |

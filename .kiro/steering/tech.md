# Tecnología · Sistema de Gestión de Taller y Repuestos Jorge Motors

Redacta en español.

> Versión 2.0 (2026-11-27). Versiones tomadas de `requirements.txt` y del entorno instalado (`python --version` y `importlib.metadata`) en la máquina de desarrollo.

## Entorno

| Componente | Versión exigida | Versión instalada (verificada) |
|---|---|---|
| Python | 3.11 o superior (ADR-001) | 3.12.10 |
| SQLite (incluida en Python) | — | 3.49.1 |
| Sistema operativo de desarrollo | Windows o Linux | Windows 11 |
| PHP | No se usa | No aplica (XAMPP trae PHP 8.0.30, pero el proyecto no lo utiliza) |

## Dependencias (`requirements.txt`)

| Paquete | Fijado en requirements.txt | Instalado | Uso |
|---|---|---|---|
| fastapi | 0.143.0 | 0.143.0 | API REST y archivos estáticos |
| uvicorn | 0.54.0 | 0.54.0 | Servidor ASGI |
| httpx | 0.28.1 | 0.28.1 | Llamadas del agente al proveedor de IA; cliente de pruebas |
| python-dotenv | 1.2.4 | 1.2.4 | Lectura de `.env` |
| pydantic | 2.14.0 | 2.14.0 | Validación de cuerpos y respuestas |
| mcp[cli] | <2 | 1.30.0 | Servidor MCP (FastMCP) y cliente stdio del agente; la versión 2 no es compatible |
| google-genai | 1.72.0 | 1.72.0 | Solo lo usa `GeminiGateway`, que es código heredado sin uso en ejecución |
| pytest | 9.1.1 | 9.1.1 | Pruebas |
| hypothesis | 6.168.5 | 6.168.5 | Pruebas basadas en propiedades |

## Backend
- FastAPI en un único proceso: `python -m uvicorn app.main:app --port 8000`, sin `--reload`, porque en Windows impide encender el Servidor MCP.
- Siete módulos de dominio en `app/modules/` y un manejador global que traduce los errores 422 al español (`app/main.py`).

## Frontend
- HTML + JavaScript sin frameworks (`frontend/index.html`, `frontend/static/app.js`, `frontend/static/styles.css`), servido por FastAPI.
- `localStorage` guarda el rol, la última pestaña y hasta 15 conversaciones del chat.

## IA
- Agente JorgeBot (`agente/agente.py`) con herramientas MCP. Llama al modelo por HTTPS con la API de *chat completions* compatible con OpenAI.

| Proveedor | Variable de la clave | Variable del modelo | Modelo por defecto |
|---|---|---|---|
| OpenAI | `OPENAI_API_KEY` | `OPENAI_MODEL` | `gpt-4o-mini` |
| Gemini | `GEMINI_API_KEY` | `GEMINI_MODEL` | `gemini-2.5-flash` |
| Groq | `GROQ_API_KEY` | `GROQ_MODEL` | `llama-3.3-70b-versatile` |

- Selección: `AGENTE_PROVEEDOR` si está definido y tiene clave; si no, el primero con clave en el orden OpenAI → Gemini → Groq. En el `.env` actual hay claves de OpenAI y de Gemini, así que **se usa OpenAI**. El valor de `OPENAI_MODEL` no se documenta.
- Parámetros fijos: `temperature` 0.2, `max_tokens` 450, 20 s de límite por llamada, hasta 4 rondas de herramientas, memoria de 10 mensajes por conversación y 200 conversaciones a la vez.
- Las claves solo se leen de variables de entorno.

## Base de datos
- SQLite `data/taller.db` en modo WAL, con 7 tablas: `clientes`, `vehiculos`, `ordenes_trabajo`, `repuestos`, `stock`, `trazabilidad_ia` y `comparaciones_conteo`. La crea y llena `data/seed.py`; si no existe, `app/main.py` la crea al arrancar.
- La app no usa MySQL. `data/exportar_a_xampp.py` hace una copia opcional de solo revisión en MySQL/MariaDB de XAMPP (base `jorge_motors_app`).

## Integración de datos
- Servidor MCP propio y de solo lectura (`agente/servidor_mcp.py`, FastMCP, transporte stdio) con 7 herramientas. Lo enciende el agente como proceso hijo y lo reinicia si se cae.
- Los módulos H2–H6 leen con `McpReadClient` en modo stub (SQLite `mode=ro`). No hay un Servidor MCP en red.

## Variables de entorno

| Variable | Obligatoria | Uso |
|---|---|---|
| `OPENAI_API_KEY` / `GEMINI_API_KEY` / `GROQ_API_KEY` | Al menos una | Clave del proveedor de IA; sin ninguna, la app no arranca |
| `OPENAI_MODEL` / `GEMINI_MODEL` / `GROQ_MODEL` | No | Cambia el modelo por defecto |
| `AGENTE_PROVEEDOR` | No | Fuerza `openai`, `gemini` o `groq` |
| `MODO_TEST` | No | `1` en pruebas: no exige clave ni enciende el Servidor MCP |
| `TALLER_DB` | No | Ruta de la base que lee el Servidor MCP (las pruebas la apuntan a una base temporal) |
| `XAMPP_MYSQL`, `XAMPP_USUARIO`, `XAMPP_CLAVE`, `XAMPP_BD` | No | Solo para `data/exportar_a_xampp.py` |

## Control de versiones
- Git/GitHub. Rama de trabajo `develop`; `main` se actualiza con pull requests.

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
| 2026-11-27 | Ingeniería inversa, versión 2.0: faltaban las versiones reales, los parámetros del modelo, el proveedor en uso y las variables de entorno | Tablas de entorno, dependencias, proveedores y variables de entorno; parámetros del agente |

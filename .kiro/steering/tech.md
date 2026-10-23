# Tecnología · Sistema de Gestión de Inventario Jorge Motors

Redacta en español.

## Backend
- Python 3.11+
- FastAPI

## Frontend
- HTML + JS simple (sin frameworks pesados)

## IA
- Gemini API para funcionalidades de asistencia (ej. explicar disponibilidad de un repuesto al cliente)
- La clave de la API se guarda en variable de entorno, nunca en el código

## Base de datos
- SQLite con datos simulados (clientes, vehículos, repuestos, stock)

## Integración de datos
- Servidor MCP propio, de solo lectura, conectado en la semana 4, usado por las funcionalidades marcadas con * (consultar stock, actualizar inventario, generar reporte de bajo stock)

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
- `.env` nunca se versiona; la clave de Gemini solo vive en variable de entorno.

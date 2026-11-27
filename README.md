# Asistente de Gestión de Taller y Repuestos · Jorge Motors

Aplicación web (FastAPI + HTML/JS + SQLite) para registrar Órdenes de Trabajo (OT), consultar historial y stock, ver alertas de stock mínimo, comparar el conteo físico, generar reportes por técnico y conversar con **JorgeBot**, un agente de IA que consulta la base de datos mediante herramientas MCP de solo lectura. Todos los datos son simulados (Ley N.° 29733): los nombres de los clientes son inventados y los DNI son de la serie `100000xx`.

Documentación: `.kiro/steering/` (producto, tecnología, estructura), `.kiro/specs/asistente-taller-jorge-motors/` (requisitos, diseño y tareas, versión 2.0) y `docs/` (ADR-001 a ADR-009, ficha del agente, casos de prueba, volcado de la base).

## Proyecto final: agente JorgeBot

| Entregable | Dónde está |
|---|---|
| Chat integrado en la aplicación | Pestaña «Asistente IA» (`frontend/`) |
| Servidor MCP con 7 herramientas | `agente/servidor_mcp.py` |
| Instrucciones del agente (10 reglas) | `agente/instrucciones.txt` |
| Agente (ruta B, Python) | `agente/agente.py` |
| Puente chat → agente (equivale a `chat.php`) | `app/modules/asistente/router.py` |
| Ficha del agente | `docs/ficha_agente.md` |
| Casos de prueba | `docs/casos_prueba.md` |
| Guion de la demostración | `docs/guion_demo.md` |

## Requisitos

- Python 3.11 o superior (probado con 3.12.10; ADR-001).
- Una clave de IA de **al menos uno** de estos proveedores: OpenAI (de pago), Gemini (gratis en <https://aistudio.google.com/apikey>) o Groq (gratis en <https://console.groq.com/keys>).
- No hace falta XAMPP, Apache ni MySQL: SQLite viene con Python. XAMPP solo sirve para la copia opcional de revisión (ver más abajo).

## Instalación

```bash
git clone https://github.com/diegocr02/Proyecto-Taller.git
cd Proyecto-Taller
git checkout develop
python -m pip install -r requirements.txt      # incluye mcp[cli]<2 (la versión 2 no es compatible)
cp .env.example .env                           # en PowerShell: copy .env.example .env
```

Abra `.env` con el Bloc de notas y escriba una clave real en lugar de `your_key_here`. Las claves nunca se suben al repositorio (`.env` está en `.gitignore`).

### Variables de `.env` (valores de ejemplo)

```ini
# Obligatoria: al menos UNA clave
GEMINI_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here
# GROQ_API_KEY=your_key_here

# Opcionales: modelo de cada proveedor (estos son los valores por defecto)
# GEMINI_MODEL=gemini-2.5-flash
# OPENAI_MODEL=gpt-4o-mini
# GROQ_MODEL=llama-3.3-70b-versatile

# Opcional: forzar un proveedor (openai, gemini o groq)
# AGENTE_PROVEEDOR=gemini

# Opcionales técnicas
# MODO_TEST=0                                   # 1 solo en pruebas
# TALLER_DB=data/taller.db                      # base que lee el servidor MCP
# XAMPP_MYSQL=C:\xampp\mysql\bin\mysql.exe      # solo para exportar_a_xampp.py
# XAMPP_USUARIO=root
# XAMPP_CLAVE=
# XAMPP_BD=jorge_motors_app
```

**Qué proveedor se usa:** el de `AGENTE_PROVEEDOR` si está definido; si no, el primero con clave en este orden: **OpenAI → Gemini → Groq**. Si su `.env` tiene claves de OpenAI y de Gemini, se usa OpenAI, que es de pago. Para usar Gemini, comente la clave de OpenAI o ponga `AGENTE_PROVEEDOR=gemini`.

## Orden de encendido

1. (Solo la primera vez, opcional) `python data/seed.py`: crea `data/taller.db` con 20 clientes, 20 vehículos, 20 repuestos con su stock y 23 OT. Si la base no existe, la app la crea sola al arrancar.
2. `python -m uvicorn app.main:app --port 8000`. **Sin `--reload`**, porque en Windows impide encender el servidor MCP.
3. Espere en la terminal el mensaje `Servidor MCP listo con 7 herramientas`. El agente enciende solo el servidor MCP; no hay que abrir otra terminal.
4. Abra <http://localhost:8000>, elija el rol en la esquina superior derecha y use las pestañas.

Si no hay ninguna clave en `.env`, el proceso termina al arrancar con «clave de API de asistencia no configurada» en el log. Si la clave existe pero la IA falla, solo el chat responde «Asistencia de IA no disponible en este momento»; el resto del sistema sigue funcionando.

**Empezar de cero con la base:** apague la app, borre `data/taller.db`, `data/taller.db-wal` y `data/taller.db-shm`, y corra `python data/seed.py`. Volver a correr el seed sobre una base existente **no** la reinicia, porque usa `INSERT OR IGNORE`. Así se pierden las OT y las consultas registradas.

## Funcionalidades actuales

| Pestaña | Qué hace | Roles |
|---|---|---|
| Registrar OT | Formulario de OT (cliente, vehículo y servicio). Si el DNI o la placa ya existen, actualiza sus datos | Recepcionista, Gerente |
| Historial | Busca por placa o DNI (hasta 100 OT) y muestra el detalle de cada una | Recepcionista, Técnico, Gerente |
| Inventario | Busca un repuesto por código exacto o por parte del nombre | Técnico, Encargado de Compras, Gerente |
| Alertas | Repuestos con stock ≤ mínimo; contador en la pestaña y en la campana | Encargado de Compras, Gerente |
| Comparación | Compara el conteo físico con el sistema (por código) y guarda el resultado | Encargado de Compras, Gerente |
| Reportes | OT por técnico en un rango de fechas; exporta a CSV | Gerente |
| Asistente IA | Chat con JorgeBot: memoria por conversación, conversaciones recientes, herramienta usada visible | Todos |

La app no cambia el estado de las OT ni modifica el stock. Tampoco tiene inicio de sesión: el rol se elige en la pantalla.

## Preguntas de ejemplo para el asistente IA

Comprobadas contra la base el 25/11/2026 y el 27/11/2026 (ver `docs/casos_prueba.md`):

| Pregunta | Herramienta MCP que usa | Respuesta esperada con los datos actuales |
|---|---|---|
| ¿Qué hay de stock? / Dame el inventario | `listar_inventario` | Los 20 repuestos con su estado |
| ¿Cuántas baterías quedan? | `buscar_repuesto` | Batería 12V 65Ah: 1 unidad (mínimo 3) |
| ¿Qué repuestos debo reponer? | `repuestos_por_reponer` | 8 repuestos, empezando por el Kit de embrague (0/2) |
| ¿Qué trabajos tiene la placa ABC-123? | `historial_vehiculo` | OT 14 y OT 1 (Luis Pachas, cerradas) |
| ¿Qué órdenes tiene el DNI 10000002? | `historial_cliente` | OT 22 (abierta) y OT 2 (en proceso), Nissan Sentra XYZ-789 |
| ¿Qué órdenes tiene pendientes Miguel Torres? | `ordenes_pendientes` | 4 OT: 3, 16, 19 y 23 |
| ¿Cuántas órdenes atendió cada técnico en noviembre de 2026? | `resumen_ordenes_por_tecnico` | 10 OT: Luis Luna 4, Miguel Torres 3, Luis Pachas 3 |
| ¿Qué trabajos tiene la placa ZZZ-999? | `historial_vehiculo` | Que esa placa no existe |

También recuerda la conversación («¿Y cuál es su stock mínimo?»), rechaza los temas ajenos al taller y no revela nombres ni DNI de clientes. Datos simulados: placas como ABC-123, XYZ-789 y CDE-345; DNI 10000001 a 10000020; repuestos REP-001 a REP-020.

> Las fechas de las OT simuladas se calculan a partir del día en que se corre `seed.py`. En una base nueva, las fechas y el resumen por mes serán distintos a los de esta tabla.

## Ver la base de datos en XAMPP (phpMyAdmin)

La app usa SQLite (`data/taller.db`). Para revisar los datos en phpMyAdmin existe una **copia de solo revisión** (ADR-009):

```bash
python data/exportar_a_xampp.py    # con MySQL encendido en el panel de XAMPP
```

Crea (o vuelve a crear) la base `jorge_motors_app` con las mismas 7 tablas y datos, y se ve en <http://localhost/phpmyadmin>. Lo que se cambie en phpMyAdmin no llega a la app; para actualizar la copia, se vuelve a correr el script. El volcado SQL de la base está en `docs/base_datos.sql`.

## Probar el servidor MCP solo

```bash
python agente/servidor_mcp.py      # queda esperando por stdio; se puede conectar desde VS Code como cliente MCP
python -m pytest tests/test_agente.py
```

## Pruebas

```bash
python -m pytest
```

Son 83 pruebas (resultado del 27/11/2026, después de corregir los defectos: 83 aprobadas). Incluyen pruebas unitarias, las 17 propiedades PBT de `design.md` (Hypothesis), las 7 herramientas MCP, el ciclo del agente con un modelo falso (no gasta cuota de IA) y la prueba de rendimiento de R7.1 (`docs/resultados_rendimiento.md`).

## Entregables de la sesión 7

`docs/S7_Guia_de_laboratorio_LosPapus.docx` (guía completada), `docs/trazabilidad_s7.md`, `docs/registro_s7.md`, `docs/deuda_tecnica.md` y `docs/reto2_rompan_modulo_s7.md`.

## Arquitectura en una línea

Navegador → FastAPI (`app/`). Las pantallas clásicas leen con `McpReadClient` (SQLite en solo lectura). El chat pasa por `AgenteTaller` → servidor MCP por stdio (`agente/servidor_mcp.py`) → SQLite en solo lectura, y el modelo de IA se llama por HTTPS. Detalle completo en `.kiro/specs/asistente-taller-jorge-motors/design.md`.

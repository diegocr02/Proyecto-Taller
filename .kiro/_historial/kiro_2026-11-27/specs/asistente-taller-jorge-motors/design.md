# Design Document

---

## Overview

El sistema es una aplicación web de página única que digitaliza las Órdenes de Trabajo (OT) y el control de inventario de repuestos de Jorge Motors. Está compuesto por un backend FastAPI (Python 3.11+), un frontend HTML + JavaScript simple servido por el mismo proceso, y una base de datos SQLite local (`data/taller.db`).

Hay dos caminos de lectura, ambos de solo lectura (`mode=ro`):

- **Módulos H-02 a H-06** (historial, inventario, alertas, comparación, reportes): leen mediante `McpReadClient` (`app/shared/mcp_client.py`), que consulta SQLite dentro del mismo proceso.
- **Asistente IA (H-09, agente JorgeBot)**: el `AgenteTaller` (`agente/agente.py`) enciende como proceso hijo el Servidor MCP del proyecto (`agente/servidor_mcp.py`, FastMCP, transporte stdio) y usa sus 7 herramientas de solo lectura. El modelo de lenguaje se llama por HTTPS con la API compatible con OpenAI de uno de tres proveedores: OpenAI, Gemini o Groq (el primero con clave en `.env`, o el indicado en `AGENTE_PROVEEDOR`).

Las escrituras (OT, conteo físico y trazabilidad de IA) se hacen directamente sobre SQLite mediante los repositorios de cada módulo. Si el proveedor de IA falla, solo el asistente responde "Asistencia de IA no disponible en este momento"; el resto del sistema sigue funcionando. Los datos son exclusivamente simulados, en cumplimiento de la Ley N.° 29733.

---

## Architecture

### Diagrama C4 Nivel 1 — Contexto del sistema

```mermaid
flowchart TD
    subgraph Personas["Personas"]
        REC["Recepcionista
(asesor de servicio)"]
        TEC["Técnico mecánico"]
        ENC["Encargado Compras
/ Almacén"]
        GER["Gerente"]
    end

    subgraph SJM["Sistema Jorge Motors
(esta aplicación)"]
        APP["Asistente de Gestión
de Taller y Repuestos"]
    end

    subgraph Externos["Sistemas externos"]
        GEM["Proveedor de IA
(OpenAI · Gemini · Groq)"]
    end

    REC -- "Registra OT" --> APP
    TEC -- "Consulta historial
y stock" --> APP
    ENC -- "Consulta alertas
y compara inventario" --> APP
    GER -- "Genera reportes
por técnico" --> APP
    APP -- "Pide respuestas al agente
(HTTPS, API compatible con OpenAI)" --> GEM
```

> El Servidor MCP no es un sistema externo: forma parte de la aplicación y lo enciende el propio agente (ver C4 Nivel 2).

### Diagrama C4 Nivel 2 — Contenedores
```mermaid
flowchart TD
    subgraph Usuario["Usuario del Taller"]
        B["Navegador\n(HTML + JavaScript)"]
    end

    subgraph SistemaJorgeMotors["Sistema Jorge Motors"]
        F["FastAPI App\n(Python 3.11+)\npuerto 8000"]
        DB["SQLite DB\ndata/taller.db (modo WAL)"]
        MCP["Servidor MCP\nagente/servidor_mcp.py\n(proceso hijo, stdio, solo lectura)"]
    end

    subgraph Externo["Servicios Externos"]
        G["Proveedor de IA\n(OpenAI · Gemini · Groq)"]
    end

    B -- "HTTP / REST (JSON)" --> F
    F -- "SQL directo (escritura)\ny lectura mode=ro (McpReadClient)" --> DB
    F -- "MCP por stdio\n(agente JorgeBot)" --> MCP
    MCP -- "SQL (solo SELECT, mode=ro)" --> DB
    F -- "HTTPS / REST" --> G
```

---

### Diagrama C4 Nivel 3 — Componentes

```mermaid
flowchart TD
    subgraph Navegador["Navegador (HTML + JS)"]
        UI["Interfaz de usuario"]
    end

    subgraph FastAPIApp["FastAPI App (Python 3.11+)"]
        subgraph Modulos["Módulos de dominio"]
            MOT["Módulo OT\n/ordenes"]
            MHist["Módulo Historial\n/historial"]
            MInv["Módulo Inventario\n/inventario"]
            MAl["Módulo Alertas\n/alertas"]
            MComp["Módulo Comparación\n/comparacion"]
            MRep["Módulo Reportes\n/reportes"]
            MAI["Módulo Asistente IA\n/asistente"]
        end

        subgraph Shared["Compartido (shared/)"]
            McpClient["McpReadClient\nmcp_client.py\n(SQLite mode=ro)"]
        end

        subgraph Agente["Agente (agente/)"]
            AG["AgenteTaller\nagente.py"]
        end

        subgraph Repos["Repositorios de escritura"]
            ROT["RepositorioOT\n(INSERT / UPDATE)"]
            RComp["RepositorioComparacion\n(INSERT)"]
            RTraz["RepositorioTrazabilidad\n(INSERT)"]
        end
    end

    subgraph Datos["Capa de datos"]
        SQLite["SQLite DB\ntaller.db"]
        MCP["Servidor MCP\nservidor_mcp.py\n7 herramientas"]
    end

    subgraph Externo["Externo"]
        IA["Proveedor de IA\n(OpenAI · Gemini · Groq)"]
    end

    UI -- "HTTP" --> MOT & MHist & MInv & MAl & MComp & MRep & MAI

    MHist & MInv & MAl & MComp & MRep --> McpClient
    MAI --> AG
    MAI --> RTraz

    MOT --> ROT
    MComp --> RComp

    ROT --> SQLite
    RComp --> SQLite
    RTraz --> SQLite
    McpClient --> SQLite
    AG -- "stdio" --> MCP
    MCP --> SQLite
    AG -- "HTTPS" --> IA
```

---

### Diagrama de secuencia — Registrar Orden de Trabajo (H1)

```mermaid
sequenceDiagram
    autonumber
    actor Recepcionista
    participant Navegador
    participant FastAPI as FastAPI App<br/>(POST /ordenes)
    participant RepoOT as RepositorioOT
    participant SQLite

    Recepcionista->>Navegador: Completa formulario y hace clic en "Registrar"
    Navegador->>FastAPI: POST /ordenes {nombre, dni, placa, marca, modelo,<br/>anio, kilometraje, motivo, tecnico, observaciones?}
    FastAPI->>FastAPI: Valida campos obligatorios y rangos
    alt Validación fallida
        FastAPI-->>Navegador: 422 Unprocessable Entity<br/>{campo faltante o inválido}
        Navegador-->>Recepcionista: Muestra mensaje de error con campo indicado
    else Validación exitosa
        FastAPI->>RepoOT: crear_ot(datos_validados)
        RepoOT->>SQLite: INSERT INTO ordenes_trabajo (...)
        SQLite-->>RepoOT: rowid / id generado
        RepoOT-->>FastAPI: OT creada {id, fecha_hora}
        FastAPI-->>Navegador: 201 Created {id_ot, mensaje: "OT creada exitosamente"}
        Navegador-->>Recepcionista: Muestra confirmación con ID de OT generado
    end
```

---

### Diagrama de despliegue

```mermaid
flowchart TD
    subgraph Lab["Máquina del laboratorio (Windows / Linux)"]
        subgraph ProcFastAPI["Proceso: python -m uvicorn app.main:app --port 8000"]
            FastAPI["FastAPI App\nPython 3.11+\npuerto 8000"]
        end

        subgraph ProcMCP["Proceso hijo (lo enciende el agente al arrancar)"]
            MCP["Servidor MCP\nagente/servidor_mcp.py\nstdio, sin puerto\n(solo lectura)"]
        end

        DB["Archivo SQLite\ndata/taller.db\n(en disco local)"]

        EnvFile[".env\n(OPENAI_API_KEY / GEMINI_API_KEY /\nGROQ_API_KEY, AGENTE_PROVEEDOR)"]
    end

    subgraph ClienteLab["Navegador del usuario (misma red)"]
        Browser["Chrome / Firefox\nhttp://localhost:8000"]
    end

    subgraph Cloud["Internet (externo)"]
        IA["Proveedor de IA\n(OpenAI · Gemini · Groq)"]
    end

    Browser -- "HTTP :8000" --> FastAPI
    FastAPI -- "lee variables de entorno" --> EnvFile
    FastAPI -- "SQL directo" --> DB
    FastAPI -- "stdin / stdout" --> MCP
    MCP -- "SQL SELECT" --> DB
    FastAPI -- "HTTPS" --> IA
```

> **Nota de despliegue:** el proyecto usa Python 3.11+ con `uvicorn` como servidor ASGI. Solo se abre **una** terminal: al arrancar, `app/main.py` enciende en segundo plano el Servidor MCP del agente (en el log aparece `Servidor MCP listo con 7 herramientas`). No se usa `--reload`, porque en Windows impide encender el Servidor MCP. La app no usa XAMPP, Apache ni MySQL; SQLite es un archivo local sin servidor. Para revisar los datos en phpMyAdmin existe una copia opcional de solo revisión: `python data/exportar_a_xampp.py` crea la base `jorge_motors_app` en MySQL/MariaDB de XAMPP. La app no lee esa copia.

---

## Components and Interfaces

| Componente | Responsabilidad | Carpeta | Historias que satisface |
|---|---|---|---|
| `Módulo OT` | Expone los endpoints de creación y consulta de OT | `app/modules/ordenes/` | H1 |
| `Módulo Historial` | Expone el endpoint de búsqueda del historial por placa o DNI | `app/modules/historial/` | H2 |
| `Módulo Inventario` | Expone el endpoint de consulta de stock de repuestos | `app/modules/inventario/` | H3 |
| `Módulo Alertas` | Calcula y expone la lista de repuestos en alerta de stock mínimo | `app/modules/alertas/` | H4 |
| `Módulo Comparación` | Recibe el conteo físico, consulta el stock registrado y devuelve diferencias con signo | `app/modules/comparacion/` | H5 |
| `Módulo Reportes` | Genera el reporte de OT por técnico en un rango de fechas y produce el CSV | `app/modules/reportes/` | H6 |
| `Módulo Asistente IA` | Puente entre el chat y el agente: recibe `{pregunta, rol, sesion}`, llama a `AgenteTaller.responder()` y registra la trazabilidad; también borra la memoria de una conversación | `app/modules/asistente/` | H9 |
| `AgenteTaller` (JorgeBot) | Agente con bucle de herramientas: envía la pregunta, las instrucciones (`agente/instrucciones.txt`) y las herramientas MCP al modelo; ejecuta las herramientas que pida y devuelve la respuesta. Recuerda las últimas preguntas por sesión. Límite de 20 s por llamada al modelo | `agente/agente.py` | H9 |
| `Servidor MCP` | 7 herramientas de solo lectura (FastMCP, stdio): `buscar_repuesto`, `listar_inventario`, `repuestos_por_reponer`, `historial_vehiculo`, `historial_cliente`, `ordenes_pendientes` y `resumen_ordenes_por_tecnico`. Abre SQLite con `mode=ro`, usa parámetros `?` y `LIMIT`, y no devuelve nombres de clientes | `agente/servidor_mcp.py` | H9 |
| `McpReadClient` | Acceso de solo lectura para los módulos H2–H6: consulta SQLite con `mode=ro` dentro del proceso (modo stub, activo por defecto) y lanza `McpNoDisponibleError` (→ 503) si la base no está disponible | `app/shared/mcp_client.py` | H2, H3, H4, H5, H6 |
| `GeminiGateway` | **Componente heredado, sin uso en ejecución.** Era el acceso a Gemini antes del agente; hoy solo lo usa `tests/test_gemini_gateway.py`. El agente llama al modelo directamente | `app/shared/gemini_gateway.py` | — |
| `RepositorioOT` | En una transacción: busca el cliente por DNI y el vehículo por placa, los actualiza si existen o los crea si no, e inserta la OT | `app/modules/ordenes/repositorio.py` | H1 |
| `RepositorioComparacion` | Guarda cada resultado del conteo físico en `comparaciones_conteo` | `app/modules/comparacion/repositorio.py` | H5 |
| `RepositorioTrazabilidad` | Guarda cada consulta al agente en `trazabilidad_ia` | `app/modules/asistente/repositorio.py` | H9 |
| `Frontend HTML + JS` | Interfaz de usuario servida estáticamente, con selector de rol y chat de JorgeBot; consume la API REST de FastAPI | `frontend/` | H1–H9 |
| `taller.db` | Base de datos SQLite con datos simulados (20 registros por tabla), creada por `data/seed.py` | `data/taller.db` | Todos |

**Estructura de carpetas (real):** ver `.kiro/steering/structure.md`, que es la fuente de verdad.

```
app/            main.py, modules/<7 módulos>/, shared/mcp_client.py, shared/gemini_gateway.py
agente/         agente.py, servidor_mcp.py, instrucciones.txt
frontend/       index.html, static/app.js, static/styles.css, static/img/
data/           seed.py, exportar_a_xampp.py, taller.db (no se versiona)
tests/          12 archivos test_*.py + conftest.py
docs/           ADR-001..003, ficha del agente, casos de prueba, guion de demo, etc.
```

---

### Contratos de la API REST

> Contratos obtenidos por ingeniería inversa de los routers y modelos Pydantic (`app/modules/*/router.py` y `schemas.py`) al 2026-11-27. Todo error de validación devuelve 422 con `{detail, campos}` (manejador en `app/main.py`).

| Módulo | Verbo | Ruta | Parámetros / Cuerpo | Código éxito | Códigos de error | Requisitos |
|---|---|---|---|---|---|---|
| OT | POST | /ordenes | Body JSON: nombre (≤100), dni (8 dígitos), placa (≤10), marca (≤50), modelo (≤50), anio (1900–año en curso), kilometraje (0–999 999), motivo (≤500), tecnico (≤100), observaciones (opcional, ≤1000) | 201 {id_ot, mensaje: "OT creada exitosamente"} | 422 campo inválido/faltante; 503 error al guardar | R1.1–R1.7 |
| OT (detalle) | GET | /ordenes/{id_ot} | Path: id_ot | 200 {id, nombre, dni, placa, marca, modelo, anio, kilometraje, motivo, tecnico, estado, observaciones, fecha_hora} | 404 no encontrada | R1.2 (Propiedad 2, round-trip) |
| Historial | GET | /historial | Query: q=<placa\|dni> | 200 {ordenes: [{id, fecha, motivo, tecnico, estado, observaciones}], mensaje?}, hasta 100, de la más reciente a la más antigua | 422 formato inválido; 503 MCP no disponible | R2.1–R2.5 |
| Historial (detalle) | GET | /historial/{id_ot} | Path: id_ot | 200 {id, fecha, motivo, tecnico, estado, observaciones} | 404 no encontrada; 503 MCP no disponible | R2.2 |
| Inventario | GET | /inventario | Query: q=<nombre\|codigo> | 200 {resultados: [{nombre, codigo, cantidad, unidad}], mensaje?} | 422 entrada vacía; 503 MCP no disponible | R3.1–R3.7 |
| Alertas | GET | /alertas | — | 200 {alertas: [{nombre, codigo, cantidad, stock_minimo}], mensaje?} (cantidad ≤ stock_minimo) | 503 MCP no disponible | R4.1–R4.6 |
| Comparación | POST | /comparacion | Body JSON: items: [{codigo (≤20), conteo_fisico (≥0)}] (mín. 1 ítem) | 200 {resultados: [{nombre, codigo, sistema, conteo, diferencia, descuadre}], no_encontrados: [codigo], mensaje?} | 422 sin ítems; 503 MCP no disponible | R5.1–R5.6 |
| Reportes | GET | /reportes | Query: fecha_inicio=YYYY-MM-DD, fecha_fin=YYYY-MM-DD | 200 {reporte: [{tecnico, total, abierta, en_proceso, cerrada}], mensaje?} | 422 rango inválido; 503 MCP no disponible | R6.1–R6.6 |
| Reportes CSV | GET | /reportes/csv | Query: fecha_inicio, fecha_fin | 200 text/csv, UTF-8 con BOM (abre bien en Excel), separador coma, 5 columnas | 422 rango inválido; 503 MCP no disponible | R6.5 |
| Asistente IA | POST | /asistente | Body JSON: {pregunta (1–500), rol ∈ {Recepcionista, Técnico, Encargado_Compras, Gerente}, sesion? (≤64, memoria de la conversación)} | 200 {id_consulta, asistencia, mensaje: null, herramientas: [nombres]} o, si la IA falla, {id_consulta, asistencia: null, mensaje: "Asistencia de IA no disponible en este momento", herramientas: []} | 422 rol o pregunta inválidos | R9.1–R9.3 |
| Asistente IA (memoria) | DELETE | /asistente/sesion/{sesion} | Path: sesion; Query: rol | 204 (borra la memoria de esa conversación) | 422 rol faltante | R9 |

### Implementación del agente (Unidad 3, H-09)

En la Unidad 3 el asistente se implementó como un **agente con herramientas MCP**. No usa `GeminiGateway` ni `McpReadClient`, como estaba previsto en la versión anterior de este documento:

1. `POST /asistente` (`app/modules/asistente/router.py`) recibe la pregunta y llama a `AgenteTaller.responder(sesion, rol, pregunta)`.
2. `AgenteTaller` (`agente/agente.py`) manda al modelo las instrucciones de `agente/instrucciones.txt`, la fecha de hoy, el rol, los últimos 10 mensajes de la sesión (memoria de hasta 200 conversaciones) y la lista de herramientas del Servidor MCP. Si la petición no trae `sesion`, la pregunta va sola y se olvida al terminar.
3. Si el modelo pide una herramienta, el agente la ejecuta en `agente/servidor_mcp.py` (por stdio) y le devuelve el resultado. Puede hacerlo hasta 4 veces; en la última ya no ofrece herramientas y el modelo tiene que responder.
4. El router guarda en `trazabilidad_ia` la pregunta, las herramientas que se usaron con sus argumentos (`contexto_mcp`, JSON `{"herramientas": [{nombre, argumentos}]}`) y la respuesta o el error. Además devuelve el `id_consulta` y los nombres de las herramientas usadas.

El proveedor del modelo se elige así: `AGENTE_PROVEEDOR` si está definido; si no, la primera clave que exista en este orden: `OPENAI_API_KEY` (modelo por defecto `gpt-4o-mini`), `GEMINI_API_KEY` (`gemini-2.5-flash`), `GROQ_API_KEY` (`llama-3.3-70b-versatile`). Los tres se llaman con la misma API compatible con OpenAI por `httpx`. La ficha del agente está en `docs/ficha_agente.md` y los casos de prueba en `docs/casos_prueba.md`.

---

### Decisiones tomadas (antes «no tomadas»)

Estas decisiones estaban pendientes en la versión de la Fase 1. El estado de cada una se obtuvo del código al 2026-11-27:

- **Esquema de tablas SQLite**: **Resuelto.** Son 7 tablas, definidas en `data/seed.py`; ver «Data Models».
- **Contratos de la API REST**: **Resuelto.** Ver «Contratos de la API REST» (11 endpoints).
- **Formato exacto del CSV de exportación**: **Resuelto.** UTF-8 con BOM, separador coma y cabeceras `Técnico, Total OT, Abiertas, En proceso, Cerradas`. El archivo se llama `reporte_ot_<inicio>_<fin>.csv`.
- **Manejo de concurrencia en SQLite**: **Resuelto (2026-10-09).** `data/seed.py` activa el modo WAL, y tanto `McpReadClient` como el Servidor MCP abren la base en solo lectura (`mode=ro`). Sigue pendiente la prueba automática «crear una OT y buscarla por placa de inmediato» (criterio de reversión 2 del ADR-002).
- **Timeout de la llamada al modelo**: **Resuelto.** Es de 20 s por llamada (`TIEMPO_LIMITE_MODELO` en `agente/agente.py`; ADR-003, v1.1).
- **Estrategia de paginación**: **Resuelto.** No hay paginación: el historial devuelve como máximo las 100 OT más recientes (`LIMIT 100`), y las herramientas MCP usan `LIMIT` de 10 a 50 filas.
- **Formato del log de trazabilidad**: **Resuelto.** Es la tabla `trazabilidad_ia`; ver «Data Models».
- **Valores del stock mínimo simulado**: **Resuelto.** Van de 2 a 20 según el repuesto (`data/seed.py`).
- **Rol de usuario en la interfaz**: **Resuelto.** Se elige en un selector (`<select id="rol">`) arriba a la derecha, sin autenticación. Es deuda técnica aceptada en ADR-002.
- **Conexión con el Servidor MCP**: **Resuelto (H-09).** El Servidor MCP del proyecto (`agente/servidor_mcp.py`) lo usa solo el agente, por stdio y sin puerto. Los módulos H2–H6 siguen leyendo con `McpReadClient` en modo stub (SQLite `mode=ro`); el puerto 8001 de la versión anterior no se usa.

---

## Data Models

> Este esquema se comprobó con ingeniería inversa contra `data/taller.db` y `data/seed.py` el 2026-11-27. Son 7 tablas; las columnas, los tipos y las restricciones coinciden exactamente. Datos simulados: 20 clientes con nombres inventados de apariencia real y DNI `100000xx`, 20 vehículos, 20 repuestos con su stock y 23 OT.

### Tabla: clientes

| Columna | Tipo SQLite | Restricción | Notas |
|---|---|---|---|
| id | INTEGER | PK AUTOINCREMENT | Identificador interno |
| nombre | TEXT | NOT NULL | Máx. 100 caracteres (Requisito 1.3) |
| dni | TEXT | NOT NULL, UNIQUE | Exactamente 8 dígitos numéricos simulados (Requisito 1.3, 8.2) |

### Tabla: vehiculos

| Columna | Tipo SQLite | Restricción | Notas |
|---|---|---|---|
| id | INTEGER | PK AUTOINCREMENT | |
| placa | TEXT | NOT NULL, UNIQUE | Máx. 10 caracteres (Requisito 1.3) |
| marca | TEXT | NOT NULL | Máx. 50 caracteres |
| modelo | TEXT | NOT NULL | Máx. 50 caracteres |
| anio | INTEGER | NOT NULL | Entre 1900 y año en curso (Requisito 1.3) |
| id_cliente | INTEGER | FK → clientes.id | |

### Tabla: ordenes_trabajo

| Columna | Tipo SQLite | Restricción | Notas |
|---|---|---|---|
| id | INTEGER | PK AUTOINCREMENT | Identificador único de OT (Requisito 1.2) |
| id_vehiculo | INTEGER | FK → vehiculos.id, NOT NULL | |
| id_cliente | INTEGER | FK → clientes.id, NOT NULL | |
| kilometraje | INTEGER | NOT NULL | Entre 0 y 999 999 (Requisito 1.3) |
| motivo | TEXT | NOT NULL | Máx. 500 caracteres |
| tecnico | TEXT | NOT NULL | Nombre del técnico asignado |
| estado | TEXT | NOT NULL | Valores: abierta / en proceso / cerrada |
| observaciones | TEXT | | Puede ser NULL |
| fecha_hora | TEXT | NOT NULL | ISO 8601, generado automáticamente al crear |

### Tabla: repuestos

| Columna | Tipo SQLite | Restricción | Notas |
|---|---|---|---|
| id | INTEGER | PK AUTOINCREMENT | |
| codigo | TEXT | NOT NULL, UNIQUE | Máx. 20 caracteres (Requisito 3.1) |
| nombre | TEXT | NOT NULL | Máx. 100 caracteres |
| unidad | TEXT | NOT NULL | Ej.: unidad, litro, par |
| stock_minimo | INTEGER | NOT NULL | Umbral de alerta (Requisito 4): hay alerta si `cantidad ≤ stock_minimo`. En los datos simulados va de 2 a 20 |

### Tabla: stock

| Columna | Tipo SQLite | Restricción | Notas |
|---|---|---|---|
| id_repuesto | INTEGER | PK, FK → repuestos.id | |
| cantidad | INTEGER | NOT NULL | Cantidad disponible actual |

### Tabla: trazabilidad_ia

| Columna | Tipo SQLite | Restricción | Notas |
|---|---|---|---|
| id | TEXT | PK | UUID v4, generado por el sistema (Requisito 9.2) |
| timestamp | TEXT | NOT NULL | ISO 8601 (Requisito 9.1) |
| rol | TEXT | NOT NULL | Recepcionista / Técnico / Encargado_Compras / Gerente |
| pregunta | TEXT | NOT NULL | Texto libre |
| contexto_mcp | TEXT | NOT NULL | JSON con las herramientas MCP que usó el agente: `{"herramientas": [{"nombre", "argumentos"}]}` |
| respuesta | TEXT | | Texto generado por el agente; NULL si hubo error |
| error | TEXT | | Mensaje de error del proveedor de IA; NULL si fue exitoso (Requisito 9.3) |

### Tabla: comparaciones_conteo

Guarda cada fila de una comparación de conteo físico (Requisito 5, H-05). La escribe `RepositorioComparacion`. Existe desde el proyecto base (`data/seed.py`), pero la versión anterior de este documento no la describía.

| Columna | Tipo SQLite | Restricción | Notas |
|---|---|---|---|
| id | INTEGER | PK AUTOINCREMENT | |
| fecha_hora | TEXT | NOT NULL | ISO 8601 de la comparación |
| codigo | TEXT | NOT NULL | Código del repuesto comparado (sin FK: es una copia del momento) |
| nombre | TEXT | NOT NULL | Nombre del repuesto en ese momento |
| sistema | INTEGER | NOT NULL | Cantidad registrada en el sistema |
| conteo | INTEGER | NOT NULL | Cantidad del conteo físico |
| diferencia | INTEGER | NOT NULL | `conteo − sistema` (con signo) |
| descuadre | INTEGER | NOT NULL | 1 si `diferencia ≠ 0`, 0 si coinciden |

> **Nota sobre concurrencia:** ADR-002 identifica el riesgo de bloqueo entre las escrituras de FastAPI y las lecturas sobre el mismo archivo SQLite. Mitigación aplicada: modo WAL en `data/seed.py`, y `McpReadClient` y el Servidor MCP leen con `mode=ro`. No se han observado bloqueos al usar la app (por ejemplo, el chat lee mientras se registran OT), pero falta la prueba automática del criterio de reversión 2 (ver «Decisiones tomadas»).

## Correctness Properties

*Una propiedad es una característica o comportamiento que debe mantenerse verdadero en todas las ejecuciones válidas del sistema — esencialmente, una afirmación formal sobre lo que el sistema debe hacer. Las propiedades sirven como puente entre las especificaciones legibles por humanos y las garantías de corrección verificables automáticamente.*

### Property 1: Unicidad de identificadores de OT

*Para cualquier* conjunto de N Órdenes de Trabajo creadas en el sistema, todos sus identificadores deben ser distintos entre sí (sin colisiones).

**Validates: Requirements 1.2**

---

### Property 2: Round-trip de campos obligatorios de OT

*Para cualquier* OT creada con datos válidos generados aleatoriamente, recuperar esa OT del sistema debe retornar exactamente los mismos valores enviados en todos los campos obligatorios (nombre, DNI, placa, marca, modelo, año, km, motivo, técnico asignado y fecha/hora de creación).

**Validates: Requirements 1.3**

---

### Property 3: Rechazo de OT con campos obligatorios faltantes

*Para cualquier* subconjunto propio de los campos obligatorios de una OT (es decir, con al menos un campo omitido), el endpoint de creación debe retornar un error de validación y no incrementar el número de OT en el sistema.

**Validates: Requirements 1.4**

---

### Property 4: Límite y orden del historial de OT

*Para cualquier* historial con N OT asociadas a una placa o DNI (N ≥ 0), la búsqueda debe retornar como máximo 100 registros; si N ≤ 100, retorna exactamente N; las OT retornadas deben ser las N más recientes según su fecha de creación.

**Validates: Requirements 2.1**

---

### Property 5: Completitud de campos al consultar una OT del historial

*Para cualquier* OT almacenada en el sistema, recuperarla por identificador debe retornar un objeto que contenga exactamente los seis campos definidos: identificador de OT, fecha, motivo de ingreso, técnico asignado, estado y observaciones técnicas.

**Validates: Requirements 2.2**

---

### Property 6: Rechazo de búsqueda con formato inválido

*Para cualquier* cadena de texto que no cumpla el formato de placa (máximo 8 caracteres alfanuméricos) ni el formato de DNI (exactamente 8 dígitos numéricos), el endpoint de búsqueda de historial debe retornar un error de validación sin ejecutar la consulta al servidor MCP.

**Validates: Requirements 2.5**

---

### Property 7: Completitud e inmutabilidad de la consulta de stock

*Para cualquier* repuesto existente en el inventario, consultar su stock debe: (a) retornar un objeto con exactamente los cuatro campos definidos (nombre, código, cantidad disponible, unidad de medida) y (b) no modificar la cantidad registrada en el inventario tras la consulta.

**Validates: Requirements 3.2**

---

### Property 8: Exactitud de búsqueda por código de repuesto

*Para cualquier* código que exista en el inventario, la búsqueda por ese código debe retornar exactamente un resultado cuyo campo código coincida de forma exacta con el código buscado.

**Validates: Requirements 3.3**

---

### Property 9: Completitud de resultados en búsqueda por nombre de repuesto

*Para cualquier* término de búsqueda por nombre que coincida con K repuestos en el inventario (K ≥ 1), el resultado debe contener exactamente esos K repuestos y ningún repuesto adicional cuyo nombre no coincida.

**Validates: Requirements 3.4**

---

### Property 10: Rechazo de consulta de stock con entrada vacía o de solo espacios

*Para cualquier* cadena de texto que sea vacía o esté compuesta únicamente por espacios en blanco, el endpoint de consulta de stock debe retornar un error de validación sin ejecutar la consulta al servidor MCP.

**Validates: Requirements 3.7**

---

### Property 11: Corrección del filtrado de alertas de stock mínimo

*Para cualquier* inventario con N repuestos (cantidades y stocks mínimos generados aleatoriamente), la lista de alertas debe contener exactamente aquellos repuestos cuya cantidad disponible sea menor o igual a su stock mínimo configurado, incluyendo todos los campos requeridos (nombre, código, cantidad actual, stock mínimo).

**Validates: Requirements 4.1, 4.2**

---

### Property 12: Corrección del cálculo de diferencias en comparación de conteo físico

*Para cualquier* par de valores enteros no negativos (conteo_físico, cantidad_sistema), la diferencia calculada por el sistema debe ser exactamente `conteo_físico − cantidad_sistema`, retornada como entero con signo, y el resultado debe incluir los cinco campos definidos: nombre, código, cantidad del sistema, cantidad del conteo físico y diferencia.

**Validates: Requirements 5.1, 5.2**

---

### Property 13: Clasificación correcta del indicador de descuadre

*Para cualquier* resultado de comparación donde la diferencia es distinta de cero, el repuesto debe llevar el indicador de descuadre; cuando la diferencia es cero, no debe llevar ese indicador.

**Validates: Requirements 5.3**

---

### Property 14: Filtrado correcto de OT por rango de fechas en el reporte

*Para cualquier* rango de fechas válido `[fecha_inicio, fecha_fin]` (ambos extremos inclusivos), todas las OT incluidas en el reporte deben tener fecha de creación mayor o igual a `fecha_inicio` y menor o igual a `fecha_fin`; ninguna OT fuera del rango debe aparecer en el reporte.

**Validates: Requirements 6.1, 6.2**

---

### Property 15: Rechazo de rango de fechas inválido en el reporte

*Para cualquier* par de fechas donde `fecha_inicio` sea posterior a `fecha_fin`, el endpoint de reportes debe retornar un error de validación sin consultar el servidor MCP.

**Validates: Requirements 6.4**

---

### Property 16: Completitud y consistencia del CSV exportado

*Para cualquier* reporte generado exitosamente, el archivo CSV debe contener exactamente las cinco columnas requeridas (nombre del técnico, total de OT, OT abiertas, OT en proceso, OT cerradas), y para cada fila la suma `abierta + en_proceso + cerrada` debe ser igual al total de OT del técnico en ese período.

**Validates: Requirements 6.5**

---

### Property 17: Completitud y unicidad del log de trazabilidad de IA

*Para cualquier* conjunto de N consultas asistidas por el agente de IA procesadas por el sistema, cada entrada del log debe contener los seis campos requeridos (ID único, timestamp ISO 8601, rol del usuario, pregunta, contexto MCP utilizado y respuesta generada), y los N identificadores de entrada deben ser todos distintos entre sí.

**Validates: Requirements 9.1, 9.2**

---

## Error Handling

| Situación | Código HTTP | Respuesta al cliente | Comportamiento interno |
|---|---|---|---|
| Campo obligatorio faltante o inválido (cualquier endpoint) | 422 | `{detail: "<mensaje legible>", campos: ["<campo>", ...]}` | No se guarda nada; el frontend marca los campos con error y conserva lo ingresado |
| Error al guardar la OT | 503 | `{detail: "No se pudo registrar la orden de trabajo. Intente nuevamente."}` | Se revierte la transacción |
| Lectura de datos no disponible (`McpNoDisponibleError`) | 503 | `{detail: "El servicio de historial no está disponible en este momento"}` (o «de inventario» / «de datos», según el módulo) | Se registra el error en el log del proceso; no se expone la causa técnica |
| Proveedor de IA no disponible, timeout o error del agente | 200 (degradado) | `{id_consulta, asistencia: null, mensaje: "Asistencia de IA no disponible en este momento"}` | El error se guarda en `trazabilidad_ia.error`; el resto del sistema sigue funcionando |
| Ninguna clave de IA (`OPENAI_API_KEY`, `GEMINI_API_KEY` ni `GROQ_API_KEY`) al arrancar | — | La app no arranca | El proceso termina con `sys.exit(1)` y registra «clave de API de asistencia no configurada» en el log. Con `MODO_TEST=1` (pruebas) no se exige clave |
| Operación supera 2 segundos sin respuesta | — | Spinner/barra de progreso visible en el navegador | El frontend muestra el indicador de carga hasta recibir respuesta o hasta el timeout de 30 s |
| Operación supera 30 segundos sin respuesta | — | Mensaje de error con opción de reintentar | El frontend oculta el spinner y ofrece al usuario la opción de reintento |
| Búsqueda de historial vacía o con formato inválido | 422 | `{detail: "Formato inválido. Use placa (máx. 8 car. alfanuméricos) o DNI (8 dígitos)"}` | No se ejecuta ninguna consulta; el guion de la placa se ignora |
| Búsqueda de inventario vacía | 422 | `{detail: "Ingrese un nombre o código de repuesto válido"}` | No se ejecuta ninguna consulta |
| Comparación sin ítems | 422 | `{detail: "Debe ingresar al menos un repuesto con su conteo físico"}` | No se guarda nada |
| Rango de fechas inválido (inicio > fin) | 422 | `{detail: "La fecha de inicio no puede ser posterior a la fecha de fin"}` | No se genera el reporte |
| OT inexistente (`/ordenes/{id}` o `/historial/{id}`) | 404 | `{detail: "Orden de trabajo no encontrada"}` | — |
| Sin resultados (consultas válidas) | 200 | Lista vacía + `mensaje`: «Repuesto no encontrado», «No se encontraron registros para ese criterio de búsqueda», «No hay alertas de stock activas» o «No se encontraron órdenes de trabajo en el período indicado» | No se ejecuta ninguna escritura |

---

## Testing Strategy

### Enfoque dual

La estrategia combina pruebas basadas en ejemplos (unitarias e integración) con pruebas basadas en propiedades (PBT) para lograr cobertura complementaria: las pruebas de ejemplo validan comportamientos concretos y condiciones de borde, mientras que las pruebas de propiedades verifican invariantes universales sobre espacios de entrada amplios.

### Pruebas unitarias y de integración

Se usan para:
- Verificar comportamientos específicos y condiciones de borde (listas vacías, repuesto inexistente, rango de fechas sin OT).
- Validar el manejo de fallos de dependencias externas (lectura no disponible, proveedor de IA con error) con un `McpReadClient` que simula la caída y un agente falso.
- Confirmar el comportamiento de arranque cuando no hay ninguna clave de IA definida. Hoy se comprueba a mano (prueba de humo): no hay una prueba automática.
- Verificar la generación del indicador de carga en el frontend para operaciones lentas.

Herramienta: `pytest` con `httpx` para pruebas de los endpoints FastAPI.

### Pruebas basadas en propiedades (PBT)

Se aplican a las 17 propiedades definidas en la sección anterior. Cada prueba de propiedad se ejecuta con un mínimo de 100 iteraciones sobre datos generados aleatoriamente.

Herramienta: **Hypothesis** (biblioteca de PBT estándar para Python).

Cada prueba de propiedad debe incluir un comentario de etiqueta en el formato:

```
# Feature: asistente-taller-jorge-motors, Propiedad N: <texto de la propiedad>
```

Las propiedades que dependen del modelo de IA usan un modelo falso para que las pruebas sean rápidas y deterministas. El Servidor MCP real sí se prueba: `tests/test_agente.py` llama a sus 7 herramientas sobre una base temporal, comprueba que son de solo lectura y enciende el servidor por stdio para listar sus herramientas.

**Estado al 2026-11-27:** `python -m pytest` da **81 pruebas aprobadas** en 12 archivos (`tests/test_*.py`). `tests/test_rendimiento.py` mide el p95 (ver `docs/resultados_rendimiento.md`).

### Pruebas de humo (*smoke tests*)

- Verificar que el proceso arranca con al menos una clave de IA definida y que en el log aparece `Servidor MCP listo con 7 herramientas`.
- Verificar que el proceso termina con código distinto de cero cuando no hay ninguna clave de IA.
- Revisión documental de `data/taller.db` para confirmar que no contiene datos reales de personas.
- Casos manuales del agente (incluidas preguntas trampa sobre datos inexistentes): `docs/casos_prueba.md`.

### Cobertura mínima esperada

| Módulo | Tipo de prueba prioritaria |
|---|---|
| `RepositorioOT` | PBT (Propiedades 1, 2, 3) + integración |
| `Módulo Historial` | PBT (Propiedades 4, 5, 6) + integración con mock MCP |
| `Módulo Inventario` | PBT (Propiedades 7, 8, 9, 10) + integración con mock MCP |
| `Módulo Alertas` | PBT (Propiedad 11) + ejemplo (lista vacía) |
| `Módulo Comparación` | PBT (Propiedades 12, 13) + ejemplo (repuesto inexistente) |
| `Módulo Reportes` | PBT (Propiedades 14, 15, 16) + integración con mock MCP |
| `GeminiGateway` (heredado) | Integración con mock (error, timeout, éxito) |
| `Módulo Asistente IA` | PBT (Propiedad 17) + integración con agente falso |
| `Servidor MCP` y `AgenteTaller` | Ejemplos sobre base temporal (7 herramientas, solo lectura, sin nombres de clientes) + ciclo del agente con modelo falso |





---

## Historial de cambios

| Fecha | Hallazgo que lo origina | Cambio realizado |
|---|---|---|
| 2026-09-25 | Auditoría Fase 1 — Verificación 2: C4 Nivel 1 (contexto del sistema) ausente | Añadido diagrama C4 N1 Mermaid en sección Architecture, antes del C4 N2 |
| 2026-09-25 | Auditoría Fase 1 — Verificación 2: Data Models vacío (solo texto placeholder) | Reemplazado con esquema de 6 tablas SQLite (columnas, tipos, restricciones, notas); valores PENDIENTE marcados explícitamente |
| 2026-10-09 | Caracteres de control en las secciones de contratos de API y Data Models (acentos graves interpretados como escapes de PowerShell: `anio`, `tecnico`, `fecha`, `vehiculos`, `rol`, etc.) | Restauradas las letras perdidas; marcadas como resueltas las decisiones de modo WAL y timeout de Gemini |
| 2026-09-25 | Auditoría Fase 1 — Verificación 2: interfaces sin verbos HTTP ni códigos de respuesta | Añadida tabla de Contratos de la API REST con verbo, ruta, parámetros, código de éxito, códigos de error y requisitos para los 9 endpoints |
| 2026-11-27 | Ingeniería inversa del código y de `data/taller.db`: el documento describía el diseño de la Fase 1 (Gemini vía `GeminiGateway`, MCP en el puerto 8001) y no el sistema construido | Overview y diagramas C4 N1–N3 y de despliegue actualizados al agente JorgeBot (Servidor MCP por stdio, proveedores OpenAI/Gemini/Groq). Componentes: se agregan `AgenteTaller`, Servidor MCP y `RepositorioTrazabilidad`, y `GeminiGateway` se marca como heredado. Contratos de la API: 11 endpoints con los campos reales (`kilometraje`, `observaciones`, `no_encontrados`, `sesion`, `herramientas`, `GET /ordenes/{id_ot}`, `DELETE /asistente/sesion/{sesion}`). «Decisiones no tomadas» pasa a «Decisiones tomadas». Data Models: se agrega la tabla `comparaciones_conteo` y el rango 2–20 de `stock_minimo`. Errores y estrategia de pruebas: mensajes reales y 81 pruebas |

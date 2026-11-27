# Requirements Document

**Versión:** 2.0 · **Fecha:** 2026-11-27 · **Método:** ingeniería inversa. La fuente de verdad es el código (`app/`, `agente/`, `frontend/`, `data/seed.py`) y la base `data/taller.db`, no la versión anterior de este documento. La versión 1.0 está en el historial de git (commit `d0a0237^`), y la 1.1 de hoy, en `.kiro/_historial/kiro_2026-11-27/`.

**Formato de los criterios (EARS en español):** «CUANDO <evento>, EL Sistema DEBERÁ…» · «SI <condición>, ENTONCES EL Sistema DEBERÁ…» · «EL Sistema DEBERÁ…» (requisito permanente).

## Cambios respecto de la versión 1.0

| Requisito | Cambio | Motivo (evidencia en el código) |
|---|---|---|
| Todos | Criterios reescritos en EARS en español; «Gemini_API» pasa a «Proveedor_IA» | El agente usa OpenAI, Gemini o Groq (`agente/agente.py`, `PROVEEDORES`) |
| R1 | 1.3 agrega `observaciones` (opcional, ≤ 1000) y el estado inicial «abierta». 1.6 se reformula: solo se valida el formato del DNI. Nuevos 1.8 (actualizar el cliente o el vehículo existente) y 1.9 (detalle de OT) | `app/modules/ordenes/schemas.py`, `repositorio.py`; `GET /ordenes/{id_ot}` |
| R2 | 2.1 aclara que el guion de la placa se ignora | `app/modules/historial/schemas.py` (`criterio.replace("-", "")`) |
| R4 | Se unen los criterios repetidos 4.1, 4.4 y 4.5; nuevo 4.4 (contador de alertas); el antiguo 4.6 pasa a 4.5 | `frontend/static/app.js` (`actualizarContadorAlertas`) |
| R5 | 5.6 solo por código; nuevo 5.7 (se guarda cada comparación) | `ItemConteo.codigo`; tabla `comparaciones_conteo` |
| R6 | 6.5 precisa el formato del CSV | `app/modules/reportes/router.py` (`utf-8-sig`) |
| R8 | 8.2 precisa cómo son los datos simulados; 8.3 se ajusta a lo que hace el código | `data/seed.py`; `app/main.py` (`sys.exit(1)`) |
| R9 | 9.1 describe el contexto real que se guarda | `app/modules/asistente/router.py` (`contexto = {"herramientas": …}`) |
| R10 | **Nuevo:** agente conversacional JorgeBot | `agente/agente.py`, `agente/servidor_mcp.py`, `agente/instrucciones.txt` |
| R11 | **Nuevo:** interfaz por rol | `PANTALLAS_POR_ROL` en `frontend/static/app.js` |
| R12 | **Nuevo:** copia de revisión de la base en XAMPP | `data/exportar_a_xampp.py` |
| — | Se crea la sección «Requisitos retirados o pendientes» | Criterios de la v1.0 que el código no cumple |

## Introduction

El **Asistente de Gestión de Taller y Repuestos para Jorge Motors** digitaliza el registro de Órdenes de Trabajo (OT) y el control de inventario de repuestos, reemplazando el cuaderno y el Excel actuales. Además, ofrece el agente de IA **JorgeBot**, que responde preguntas en lenguaje natural consultando la base de datos.

Componentes: un backend FastAPI (Python 3.11+; instalado 3.12.10), un frontend HTML + JavaScript, una base SQLite con datos simulados (`data/taller.db`) y el agente JorgeBot. El agente usa un Servidor_MCP propio de solo lectura con 7 herramientas y un Proveedor_IA. Todos los datos son simulados (Ley N.° 29733).

**Fuera de alcance:** facturación electrónica e integración con SUNAT, pagos en línea, compras automáticas a proveedores, aplicación móvil, autenticación de usuarios, modificación del stock y cambio de estado de las OT.

---

## Glossary

- **Sistema**: La aplicación web Asistente de Gestión de Taller y Repuestos de Jorge Motors.
- **OT / Orden de Trabajo**: Registro del ingreso de un vehículo: motivo, técnico asignado y estado (abierta, en proceso o cerrada).
- **Recepcionista**: Asesor de servicio responsable de registrar las OT.
- **Técnico**: Mecánico asignado a una OT (Luis Pachas, Luis Luna o Miguel Torres, según el selector de `frontend/index.html`).
- **Encargado_Compras**: Encargado de Compras/Abastecimiento, responsable del inventario de repuestos.
- **Gerente**: Gerente de Jorge Motors; tiene acceso a todas las pantallas.
- **Servidor_MCP**: Servidor MCP de solo lectura del proyecto (`agente/servidor_mcp.py`, transporte stdio) con 7 herramientas. Lo enciende el agente.
- **Servicio_de_lectura**: Acceso de solo lectura que usan los módulos H-02 a H-06 (`McpReadClient`, SQLite `mode=ro`). Cuando no está disponible, los módulos responden 503.
- **Agente**: JorgeBot (`AgenteTaller`, `agente/agente.py`).
- **Proveedor_IA**: Servicio de modelo de lenguaje que usa el Agente: OpenAI, Gemini o Groq. Se usa `AGENTE_PROVEEDOR` o, si no está definido, el primero con clave en el orden OpenAI → Gemini → Groq.
- **Stock_Mínimo**: Cantidad umbral por repuesto; hay alerta cuando cantidad ≤ Stock_Mínimo.
- **Conteo_Físico**: Recuento manual de unidades que ingresa el Encargado_Compras para compararlo con el sistema.
- **Sesión_de_chat**: Conversación del chat, identificada por el campo `sesion`; el Agente recuerda sus últimos 10 mensajes.

---

## Requirements

### Requisito 1 [H-01]: Registro y consulta de Orden de Trabajo

**Historia de usuario:** Como recepcionista, quiero registrar la orden de trabajo de forma digital al recibir un vehículo, para eliminar el doble registro en cuaderno y Excel y reducir el tiempo de atención en recepción.

#### Criterios de aceptación

1. CUANDO el Recepcionista complete los campos obligatorios del criterio 3 y envíe el formulario, EL Sistema DEBERÁ crear la OT y dejarla disponible para su consulta en un plazo máximo de 2 minutos.
2. EL Sistema DEBERÁ asignar a cada OT, al crearla, un identificador numérico único e irrepetible.
3. EL Sistema DEBERÁ registrar en cada OT: nombre del cliente (1–100 caracteres), DNI (exactamente 8 dígitos), placa (1–10 caracteres), marca (1–50), modelo (1–50), año (entre 1900 y el año en curso), kilometraje (0–999 999), motivo (1–500), técnico (1–100), observaciones (opcional, hasta 1000), estado inicial «abierta» y fecha y hora de creación en ISO 8601, generadas por el Sistema.
4. SI falta un campo obligatorio o tiene un valor inválido, ENTONCES EL Sistema DEBERÁ responder 422 con un mensaje en español y la lista de campos con error, marcar esos campos en el formulario y no crear la OT.
5. CUANDO la OT se cree, EL Sistema DEBERÁ mostrar la confirmación con el identificador de la OT.
6. EL Sistema DEBERÁ rechazar un DNI que no tenga exactamente 8 dígitos numéricos.
7. SI el Sistema no puede guardar la OT o no responde en 30 segundos, ENTONCES EL Sistema DEBERÁ mostrar un mensaje de error con la opción de reintentar y conservar los datos ingresados en el formulario.
8. CUANDO se registre una OT con un DNI o una placa que ya existen, EL Sistema DEBERÁ actualizar los datos de ese cliente o vehículo en lugar de crear uno nuevo, dentro de la misma transacción que la OT.
9. CUANDO se consulte `GET /ordenes/{id_ot}`, EL Sistema DEBERÁ devolver todos los datos de la OT con su cliente y su vehículo; SI la OT no existe o el identificador no es válido, ENTONCES EL Sistema DEBERÁ responder 404.

---

### Requisito 2 [H-02]: Consulta de historial de cliente y vehículo

**Historia de usuario:** Como técnico mecánico, quiero consultar el historial del cliente y del vehículo, para diagnosticar más rápido sin depender del cuaderno físico.

#### Criterios de aceptación

1. CUANDO el usuario ingrese una placa (hasta 8 caracteres alfanuméricos, sin contar el guion) o un DNI (8 dígitos) y ejecute la búsqueda, EL Sistema DEBERÁ devolver, en un plazo máximo de 5 segundos, hasta las 100 OT más recientes asociadas, de la más reciente a la más antigua.
2. CUANDO el usuario seleccione una OT del historial, EL Sistema DEBERÁ mostrar: identificador, fecha, motivo, técnico, estado y observaciones.
3. SI no existen OT para la placa o el DNI ingresados, ENTONCES EL Sistema DEBERÁ mostrar «No se encontraron registros para ese criterio de búsqueda».
4. SI el Servicio_de_lectura no está disponible, ENTONCES EL Sistema DEBERÁ responder 503 con «El servicio de historial no está disponible en este momento».
5. SI la búsqueda está vacía o no tiene formato de placa ni de DNI, ENTONCES EL Sistema DEBERÁ responder 422 con el formato requerido y no ejecutar la búsqueda.

---

### Requisito 3 [H-03]: Consulta de stock de repuestos

**Historia de usuario:** Como técnico mecánico, quiero consultar el stock de un repuesto antes de iniciar la reparación, para no detener el trabajo por falta de información sobre el inventario disponible.

#### Criterios de aceptación

1. CUANDO el usuario ingrese el nombre o el código de un repuesto y ejecute la consulta, EL Sistema DEBERÁ mostrar la cantidad actual en stock en un plazo máximo de 5 segundos.
2. EL Sistema DEBERÁ mostrar por cada repuesto: nombre, código, cantidad y unidad de medida, sin modificar ningún dato del inventario.
3. SI el texto coincide exactamente con un código (sin distinguir mayúsculas), ENTONCES EL Sistema DEBERÁ mostrar únicamente ese repuesto.
4. SI la búsqueda por nombre coincide con más de un repuesto, ENTONCES EL Sistema DEBERÁ mostrar todos los coincidentes.
5. SI no existe ningún repuesto coincidente, ENTONCES EL Sistema DEBERÁ mostrar «Repuesto no encontrado».
6. SI el Servicio_de_lectura no está disponible, ENTONCES EL Sistema DEBERÁ responder 503 con «El servicio de inventario no está disponible en este momento».
7. SI la búsqueda está vacía o solo tiene espacios, ENTONCES EL Sistema DEBERÁ responder 422 con «Ingrese un nombre o código de repuesto válido»; SI supera los 100 caracteres, ENTONCES DEBERÁ responder 422 con «El nombre o código no puede superar 100 caracteres». En ambos casos, no ejecutará la consulta.

---

### Requisito 4 [H-04]: Alertas de stock mínimo

**Historia de usuario:** Como encargada de compras y abastecimiento, quiero recibir una alerta cuando un repuesto llegue a su stock mínimo, para generar el pedido al proveedor antes de que se agote el inventario.

#### Criterios de aceptación

1. CUANDO el usuario abra la pantalla de alertas o pulse «Actualizar», EL Sistema DEBERÁ mostrar, en un plazo máximo de 5 segundos, todos los repuestos cuya cantidad sea menor o igual a su Stock_Mínimo.
2. EL Sistema DEBERÁ incluir en cada alerta: nombre, código, cantidad actual y Stock_Mínimo.
3. SI ningún repuesto está en su Stock_Mínimo o por debajo, ENTONCES EL Sistema DEBERÁ mostrar «No hay alertas de stock activas».
4. CUANDO se cargue la página, EL Sistema DEBERÁ mostrar el número de alertas en la pestaña «Alertas» y un indicador en la campana de la cabecera, a los roles que tienen acceso a las alertas.
5. SI el Servicio_de_lectura no está disponible, ENTONCES EL Sistema DEBERÁ responder 503 con un mensaje de servicio de inventario no disponible y no mostrar alertas.

---

### Requisito 5 [H-05]: Comparación del conteo físico con el sistema

**Historia de usuario:** Como encargada de compras y abastecimiento, quiero comparar el conteo físico de repuestos con el registro del sistema, para detectar y documentar los descuadres entre el inventario real y el digital.

#### Criterios de aceptación

1. CUANDO el Encargado_Compras ingrese el Conteo_Físico de uno o más repuestos y solicite la comparación, EL Sistema DEBERÁ calcular la diferencia (Conteo_Físico − cantidad del sistema) de cada repuesto en un plazo máximo de 5 segundos.
2. EL Sistema DEBERÁ mostrar por cada repuesto: nombre, código, cantidad del sistema, Conteo_Físico y diferencia como entero con signo.
3. SI la diferencia de un repuesto es distinta de cero, ENTONCES EL Sistema DEBERÁ marcarlo con un indicador de descuadre.
4. SI no se ingresa ningún repuesto, ENTONCES EL Sistema DEBERÁ responder 422 con «Debe ingresar al menos un repuesto con su conteo físico».
5. SI el Servicio_de_lectura no está disponible, ENTONCES EL Sistema DEBERÁ responder 503 y no ejecutar la comparación.
6. SI un código ingresado no existe en el inventario, ENTONCES EL Sistema DEBERÁ excluirlo de los resultados y listarlo en `no_encontrados` con un aviso.
7. CUANDO se calcule una comparación, EL Sistema DEBERÁ guardar cada fila en la tabla `comparaciones_conteo` con su fecha y hora.

---

### Requisito 6 [H-06]: Reporte de órdenes de trabajo por técnico

**Historia de usuario:** Como gerente de Jorge Motors, quiero generar un reporte de órdenes de trabajo agrupado por técnico, para evaluar la carga de trabajo y el desempeño de cada mecánico en un período determinado.

#### Criterios de aceptación

1. CUANDO el Gerente seleccione un rango de fechas (ambos extremos incluidos) y solicite el reporte, EL Sistema DEBERÁ mostrar por cada técnico el total de OT y la cantidad por estado (abierta, en proceso, cerrada).
2. EL Sistema DEBERÁ incluir solo las OT cuya fecha de creación esté dentro del rango.
3. SI no hay OT en el rango, ENTONCES EL Sistema DEBERÁ mostrar «No se encontraron órdenes de trabajo en el período indicado».
4. SI la fecha de inicio es posterior a la de fin o una fecha no es válida, ENTONCES EL Sistema DEBERÁ responder 422 y no generar el reporte.
5. CUANDO el reporte se genere, EL Sistema DEBERÁ permitir exportarlo a CSV en UTF-8 con BOM, separado por comas, con las columnas `Técnico, Total OT, Abiertas, En proceso, Cerradas`.
6. SI el Servicio_de_lectura no está disponible, ENTONCES EL Sistema DEBERÁ responder 503 con «El servicio de datos no está disponible en este momento».

---

### Requisito 7 [H-07]: Rendimiento y disponibilidad

**Historia de usuario:** Como usuario del sistema, quiero que el sistema responda de forma oportuna, para no interrumpir el flujo de trabajo del taller.

#### Criterios de aceptación

1. EL Sistema DEBERÁ responder al menos el 95 % de las consultas de historial y de stock en 5 segundos o menos, con un único usuario concurrente.
2. SI una petición tarda más de 2 segundos, ENTONCES EL Sistema DEBERÁ mostrar un indicador de carga.
3. SI una petición supera los 30 segundos, ENTONCES EL Sistema DEBERÁ cancelarla, ocultar el indicador y mostrar un mensaje de error con la opción de reintentar.

---

### Requisito 8 [H-08]: Seguridad de credenciales y privacidad de datos

**Historia de usuario:** Como administrador del proyecto, quiero que las credenciales de la API y los datos sensibles estén protegidos, para cumplir con la Ley N.° 29733 y con las buenas prácticas de seguridad del equipo.

#### Criterios de aceptación

1. EL Sistema DEBERÁ leer las claves del Proveedor_IA solo de variables de entorno (`.env`, que está en `.gitignore`), nunca del código ni de archivos versionados.
2. EL Sistema DEBERÁ usar solo datos simulados: clientes con nombres inventados que no corresponden a personas reales y DNI de la serie `100000xx`.
3. SI al arrancar no existe ninguna clave del Proveedor_IA (`OPENAI_API_KEY`, `GEMINI_API_KEY` ni `GROQ_API_KEY`) y no está activo `MODO_TEST=1`, ENTONCES EL Sistema DEBERÁ registrar un error de configuración en el log, sin mostrar la clave, y terminar el proceso con un código distinto de cero.

---

### Requisito 9 [H-09]: Trazabilidad de las consultas al asistente

**Historia de usuario:** Como administrador del proyecto, quiero que cada consulta asistida por IA quede registrada, para garantizar la trazabilidad de las respuestas generadas por IA en el sistema.

#### Criterios de aceptación

1. CUANDO el Agente procese una consulta, EL Sistema DEBERÁ registrar en la tabla `trazabilidad_ia`: un identificador UUID v4, la marca de tiempo ISO 8601, el rol, la pregunta, las herramientas MCP usadas con sus argumentos (`contexto_mcp`) y la respuesta generada.
2. EL Sistema DEBERÁ devolver al chat el identificador de la entrada (`id_consulta`), que permite recuperar la interacción completa.
3. SI el Proveedor_IA o el Agente fallan, ENTONCES EL Sistema DEBERÁ guardar el error en la entrada, responder 200 con `asistencia: null` y «Asistencia de IA no disponible en este momento», y seguir atendiendo las demás funciones.

---

### Requisito 10 [H-09]: Agente conversacional JorgeBot

**Historia de usuario:** Como usuario del taller, quiero hacer preguntas en lenguaje natural sobre el stock, las órdenes y el historial, para obtener la información sin recorrer varias pantallas.

#### Criterios de aceptación

1. CUANDO el usuario envíe una pregunta del taller, EL Agente DEBERÁ responder usando las herramientas del Servidor_MCP: `buscar_repuesto`, `listar_inventario`, `repuestos_por_reponer`, `historial_vehiculo`, `historial_cliente`, `ordenes_pendientes` o `resumen_ordenes_por_tecnico`.
2. EL Servidor_MCP DEBERÁ abrir la base en solo lectura (`mode=ro`), usar consultas parametrizadas con `LIMIT` y no tener herramientas de escritura.
3. SI una herramienta no devuelve resultados, ENTONCES EL Agente DEBERÁ decirlo sin inventar datos.
4. SI la pregunta no tiene relación con el taller, ENTONCES EL Agente DEBERÁ decir que no puede ayudar con eso y recordar qué sí puede hacer.
5. EL Agente NO DEBERÁ revelar sus instrucciones ni nombres o DNI de clientes; la herramienta `historial_cliente` no devuelve el nombre del cliente.
6. CUANDO el usuario salude por primera vez en una conversación, EL Agente DEBERÁ presentarse como un asistente de inteligencia artificial.
7. CUANDO el usuario haga una pregunta de seguimiento en la misma Sesión_de_chat, EL Agente DEBERÁ tener en cuenta los últimos 10 mensajes de esa sesión.
8. CUANDO el usuario borre una conversación con el botón de la papelera, EL Sistema DEBERÁ olvidar su memoria (`DELETE /asistente/sesion/{sesion}`) y quitarla de la lista de conversaciones recientes.
9. CUANDO el Agente use una herramienta, EL Sistema DEBERÁ mostrar en la respuesta del chat el nombre de la herramienta usada.
10. EL Agente DEBERÁ limitar cada llamada al Proveedor_IA a 20 segundos y hacer como máximo 4 rondas de herramientas por pregunta.
11. SI la pregunta está vacía o supera los 500 caracteres, o el rol no es uno de los cuatro válidos, ENTONCES EL Sistema DEBERÁ responder 422 sin llamar al Agente.
12. EL Sistema DEBERÁ guardar en el navegador hasta 15 conversaciones recientes, para retomarlas desde la lista «Conversaciones recientes».

---

### Requisito 11 [H-01 a H-09]: Interfaz por rol

**Historia de usuario:** Como usuario del taller, quiero ver solo las pantallas de mi rol, para encontrar rápido lo que necesito.

#### Criterios de aceptación

1. EL Sistema DEBERÁ permitir elegir el rol (Recepcionista, Técnico, Encargado_Compras o Gerente) en un selector de la cabecera, sin autenticación.
2. CUANDO el usuario cambie de rol, EL Sistema DEBERÁ mostrar solo las pestañas de ese rol: Recepcionista → Registrar OT, Historial y Asistente IA; Técnico → Historial, Inventario y Asistente IA; Encargado_Compras → Inventario, Alertas, Comparación y Asistente IA; Gerente → todas.
3. CUANDO el usuario vuelva a abrir la página, EL Sistema DEBERÁ recordar el último rol y la última pestaña (si el rol tiene acceso a ella).

---

### Requisito 12 [H-08]: Copia de revisión de la base en XAMPP

**Historia de usuario:** Como integrante del equipo, quiero ver la base de datos en phpMyAdmin, para verificar los datos con una herramienta conocida.

#### Criterios de aceptación

1. CUANDO se ejecute `python data/exportar_a_xampp.py` con MySQL encendido, EL Sistema DEBERÁ crear de nuevo la base `jorge_motors_app` con las 7 tablas, sus claves foráneas y todos los datos de `data/taller.db`.
2. EL script DEBERÁ abrir `data/taller.db` en solo lectura y no modificar ninguna otra base de MySQL.
3. SI MySQL no está encendido o `mysql.exe` no existe, ENTONCES EL script DEBERÁ terminar con un mensaje de error en español.

---

## Requisitos retirados o pendientes

| Criterio de la v1.0 | Estado | Motivo |
|---|---|---|
| 1.6 «ningún nombre o DNI ingresado podrá coincidir con datos reales» | **Retirado**; lo reemplazan 1.6 (formato del DNI) y 8.2 (datos simulados) | El software no puede saber si un nombre o DNI pertenece a una persona real; solo valida el formato |
| 4.4 y 4.5 (repetían 4.1) | **Retirados** (unidos en 4.1) | Eran el mismo comportamiento |
| 5.6 «buscar por código **o nombre**» | **Pendiente** (hoy solo por código) | `ItemConteo` solo tiene `codigo`; `McpReadClient.comparar_conteo` busca `UPPER(r.codigo) = UPPER(?)` |
| 8.3 «mostrar en la interfaz un mensaje genérico de servicio no disponible» | **Pendiente** | El proceso termina antes de servir la página, así que el navegador solo muestra que no puede conectarse |
| 9.1 «los datos recuperados del Servidor_MCP utilizados como contexto» | **Pendiente** (hoy se guardan las herramientas y sus argumentos, no los datos) | `contexto = {"herramientas": resultado.herramientas_usadas}` en `app/modules/asistente/router.py` |
| Lecturas H-02 a H-06 «a través del Servidor_MCP» | **Pendiente** (hoy por `McpReadClient` en modo stub) | `usar_stub=True` por defecto; el Servidor_MCP lo usa solo el Agente (`docs/deuda_tecnica.md`) |

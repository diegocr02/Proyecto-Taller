# Requirements Document

## Introduction

Jorge Motors es un taller automotriz que actualmente registra sus Órdenes de Trabajo (OT) en cuaderno físico y hojas de cálculo Excel, y lleva el inventario de repuestos de forma manual. Esta situación genera descuadres de stock, demoras en la atención y errores que impactan al área de Taller, a Compras y al cliente final.

Esta feature implementa un sistema digital de gestión de taller e inventario que permite al Técnico Mecánico y a la Encargada de Compras registrar OT, consultar y actualizar el inventario de repuestos, y consultar el historial vehicular, eliminando el registro manual y resolviendo los descuadres de stock. El sistema persiste los datos en SQLite a través de una API FastAPI, y consume en modo solo lectura el servidor MCP ya existente (semana 4) para consultas de catálogo e historial vehicular. Los datos de clientes son simulados y tratados conforme a la Ley N.° 29733.

---

## Glossary

- **Sistema**: La aplicación web de gestión de taller e inventario de Jorge Motors (backend FastAPI + frontend HTML/JS).
- **API**: La interfaz RESTful implementada en FastAPI que expone los endpoints del Sistema.
- **OT**: Orden de Trabajo. Documento digital que registra la placa del vehículo, datos del cliente simulado, fallas reportadas y el técnico asignado.
- **Número_OT**: Identificador único, autoincremental y secuencial asignado por el Sistema a cada OT en el momento de su creación.
- **Repuesto**: Ítem del inventario identificado por un código único, nombre y cantidad disponible en stock.
- **Stock**: Cantidad de unidades disponibles de un Repuesto en el inventario del Sistema.
- **Lote**: Conjunto de unidades de un Repuesto que ingresan al inventario en una sola operación de abastecimiento.
- **Despacho**: Operación que reduce el Stock de uno o más Repuestos al ser utilizados en una OT.
- **MCP_Server**: Servidor MCP de solo lectura existente (semana 4) que expone el catálogo de repuestos y el historial vehicular. El Sistema lo consume únicamente para lectura; nunca escribe a través de él.
- **Gemini_API**: API de inteligencia artificial de Google cuya clave de acceso se lee exclusivamente desde la variable de entorno `GEMINI_API_KEY`.
- **Técnico**: Usuario con rol Técnico Mecánico.
- **Encargada_Compras**: Usuario con rol Encargada de Compras y Abastecimiento.
- **Ley_29733**: Ley N.° 29733 de Protección de Datos Personales del Perú.

---

## Requirements

### Requisito 1: Registro Digital de Órdenes de Trabajo

**Historia de Usuario:** Como Técnico, quiero registrar una OT digitalmente, para eliminar el uso de cuadernos físicos y hojas de cálculo.

#### Criterios de Aceptación

1. CUANDO el Técnico envíe un formulario de OT con placa, datos de cliente simulado y descripción de fallas, EL Sistema SHALL crear un registro de OT en la base de datos SQLite y asignar un Número_OT único autoincremental.
2. CUANDO el Técnico envíe un formulario de OT, EL Sistema SHALL responder con el Número_OT asignado en un tiempo menor a 2,0 segundos desde la recepción de la solicitud.
3. CUANDO el Técnico envíe un formulario de OT con el campo de placa vacío, EL Sistema SHALL rechazar la solicitud y devolver un mensaje de error que indique que la placa es obligatoria.
4. CUANDO el Técnico envíe un formulario de OT con el campo de descripción de fallas vacío, EL Sistema SHALL rechazar la solicitud y devolver un mensaje de error que indique que la descripción de fallas es obligatoria.
5. CUANDO el Técnico envíe un formulario de OT con una placa cuyo formato no sea alfanumérico con guion (patrón LLL-NNN, donde L es letra y N es dígito), EL Sistema SHALL rechazar la solicitud y devolver un mensaje de error que indique el formato de placa esperado.
6. THE Sistema SHALL garantizar que cada Número_OT generado sea único dentro de la base de datos SQLite.
7. THE Sistema SHALL almacenar únicamente datos de clientes simulados; no SHALL almacenar datos personales reales en cumplimiento de la Ley_29733.
8. CUANDO el Técnico envíe un formulario de OT con el campo de datos de cliente simulado vacío, EL Sistema SHALL rechazar la solicitud y devolver un mensaje de error que indique que los datos de cliente son obligatorios.
9. IF la base de datos SQLite no está disponible al momento de enviar el formulario de OT, THEN EL Sistema SHALL rechazar la solicitud y devolver un mensaje de error que indique que el registro no pudo completarse.

---

### Requisito 2: Consulta de Catálogo y Stock de Repuestos en Tiempo Real

**Historia de Usuario:** Como Técnico, quiero consultar el catálogo y el stock de repuestos en tiempo real, para verificar la disponibilidad de insumos antes de iniciar un trabajo.

#### Criterios de Aceptación

1. CUANDO el Técnico ingrese un término de búsqueda de entre 1 y 100 caracteres y ejecute la consulta, EL Sistema SHALL devolver la lista de Repuestos coincidentes con su Stock actual en un tiempo menor a 1,0 segundo, mostrando para cada Repuesto al menos su nombre, código identificador y cantidad en Stock.
2. CUANDO el Técnico ejecute una búsqueda de repuestos, EL Sistema SHALL obtener los datos del MCP_Server en modo solo lectura, sin modificar ningún dato del catálogo.
3. IF el término de búsqueda ingresado está vacío o excede los 100 caracteres, THEN EL Sistema SHALL rechazar la consulta y mostrar un mensaje de error que indique el formato de búsqueda válido, sin realizar ninguna llamada al MCP_Server.
4. IF el MCP_Server no responde dentro de 1,0 segundo o devuelve un error de conexión, THEN EL Sistema SHALL mostrar un mensaje de error que informe la indisponibilidad del servicio de consulta y no mostrará resultados parciales.
5. CUANDO el Técnico ejecute una búsqueda y no existan Repuestos que coincidan con el término ingresado, EL Sistema SHALL devolver una lista vacía acompañada de un mensaje que indique que no se encontraron resultados para el término consultado.
6. THE Sistema SHALL consumir el MCP_Server exclusivamente en modo lectura para las consultas de catálogo y no SHALL realizar operaciones de escritura ni modificación de datos a través del MCP_Server.

---

### Requisito 3: Registro de Despacho (Salida de Repuestos)

**Historia de Usuario:** Como Encargada_Compras, quiero registrar la salida de repuestos asociada a una OT, para mantener el Stock actualizado y evitar descuadres.

#### Criterios de Aceptación

1. CUANDO la Encargada_Compras registre un despacho indicando el código de Repuesto, la cantidad despachada y el Número_OT asociado, EL Sistema SHALL reducir el Stock del Repuesto en la cantidad exacta indicada y persistir el movimiento en SQLite de forma atómica, de modo que tanto la reducción de Stock como el registro del movimiento se confirmen juntos o ninguno se aplique.
2. CUANDO la Encargada_Compras intente registrar un despacho cuya cantidad supere el Stock disponible del Repuesto, EL Sistema SHALL rechazar la operación sin modificar el Stock, y devolver un mensaje de error que indique el Stock disponible actual.
3. CUANDO la Encargada_Compras registre un despacho con un código de Repuesto inexistente en la base de datos, EL Sistema SHALL rechazar la operación sin modificar ningún dato, y devolver un mensaje de error que indique que el Repuesto no fue encontrado.
4. CUANDO la Encargada_Compras registre un despacho con un Número_OT inexistente en la base de datos, EL Sistema SHALL rechazar la operación sin modificar ningún dato, y devolver un mensaje de error que indique que la OT no fue encontrada.
5. CUANDO la Encargada_Compras registre un despacho con una cantidad menor o igual a cero, o con una cantidad que no sea un número entero, EL Sistema SHALL rechazar la operación sin modificar ningún dato, y devolver un mensaje de error que indique que la cantidad debe ser un entero positivo mayor que cero.
6. THE Sistema SHALL registrar cada movimiento de Despacho con los campos código de Repuesto, cantidad, Número_OT y marca de tiempo UTC en SQLite directamente a través de la API.
7. IF el Número_OT asociado al despacho corresponde a una OT con estado cerrado o cancelado, THEN EL Sistema SHALL rechazar la operación sin modificar ningún dato, y devolver un mensaje de error que indique que no se puede despachar contra una OT en ese estado.

---

### Requisito 4: Registro de Ingreso de Nuevos Repuestos (Lotes)

**Historia de Usuario:** Como Encargada_Compras, quiero registrar el ingreso de nuevos lotes de repuestos, para mantener el Stock actualizado cuando llegan abastecimientos.

#### Criterios de Aceptación

1. CUANDO la Encargada_Compras registre un Lote indicando el código de Repuesto y la cantidad recibida, EL Sistema SHALL incrementar el Stock del Repuesto en la cantidad exacta indicada de forma atómica y persistir el movimiento en SQLite, de modo que si la persistencia falla el Stock no quede modificado.
2. CUANDO la Encargada_Compras registre un Lote para un código de Repuesto que no existe en la base de datos, EL Sistema SHALL crear el Repuesto con el código, nombre y cantidad indicados, asignar el Stock inicial igual a la cantidad del Lote, y persistir el movimiento en SQLite.
3. CUANDO la Encargada_Compras registre un Lote para un código de Repuesto que no existe y el campo nombre esté vacío, EL Sistema SHALL rechazar la operación y devolver un mensaje de error que indique que el nombre es obligatorio al crear un nuevo Repuesto.
4. CUANDO la Encargada_Compras registre un Lote con una cantidad menor o igual a cero, o con una cantidad que no sea un número entero, EL Sistema SHALL rechazar la operación y devolver un mensaje de error que indique que la cantidad debe ser un entero positivo mayor a cero.
5. CUANDO la Encargada_Compras registre un Lote con el campo de código de Repuesto vacío, EL Sistema SHALL rechazar la operación y devolver un mensaje de error que indique que el código es obligatorio.
6. THE Sistema SHALL registrar cada movimiento de ingreso de Lote con los campos: código de Repuesto, nombre del Repuesto, cantidad recibida y marca de tiempo UTC en formato ISO 8601, directamente en SQLite a través de la API; no SHALL escribir movimientos de inventario a través del MCP_Server.

---

### Requisito 5: Consulta de Historial Vehicular por Placa

**Historia de Usuario:** Como Técnico, quiero consultar el historial técnico de un vehículo por su placa, para diagnosticar fallas recurrentes y mejorar el diagnóstico.

#### Criterios de Aceptación

1. CUANDO el Técnico consulte el historial vehicular ingresando una placa registrada, EL Sistema SHALL devolver todas las OTs previas asociadas a esa placa en un tiempo menor a 2,0 segundos desde que se recibe la solicitud.
2. CUANDO el Técnico consulte el historial vehicular ingresando una placa registrada, EL Sistema SHALL obtener los datos del MCP_Server en modo solo lectura e incluir por cada OT: identificador de OT, fecha, descripción del trabajo realizado y técnico responsable.
3. CUANDO el Técnico consulte el historial vehicular de una placa que no tiene OTs registradas, EL Sistema SHALL devolver una lista vacía acompañada de un mensaje indicando que no se encontraron registros para esa placa.
4. CUANDO el Técnico consulte el historial vehicular y el MCP_Server no esté disponible, EL Sistema SHALL devolver un mensaje de error indicando la indisponibilidad del servicio de historial y no SHALL mostrar datos parciales ni información de OTs previas.
5. THE Sistema SHALL consumir el MCP_Server exclusivamente en modo lectura para las consultas de historial vehicular; no SHALL escribir ni modificar datos a través del MCP_Server.
6. IF la placa ingresada no cumple el formato alfanumérico de 6 a 7 caracteres con guion en la cuarta posición (ej. "ABC-123"), THEN EL Sistema SHALL rechazar la solicitud con un mensaje de error indicando el formato de placa válido sin realizar la consulta al MCP_Server.

---

### Requisito 6: Seguridad de la Clave de API de Gemini

**Historia de Usuario:** Como Técnico o Encargada_Compras, quiero que el sistema gestione de forma segura la clave de la Gemini_API, para que las credenciales no queden expuestas en el código fuente ni en los repositorios.

#### Criterios de Aceptación

1. THE Sistema SHALL leer la clave de acceso de la Gemini_API exclusivamente desde la variable de entorno `GEMINI_API_KEY` en tiempo de ejecución.
2. IF la variable de entorno `GEMINI_API_KEY` no está definida al iniciarse el Sistema, THEN THE Sistema SHALL detener el inicio de la aplicación y registrar un mensaje de error en el log indicando cuál variable de entorno es requerida, sin revelar ningún valor de credencial en dicho mensaje.
3. IF la variable de entorno `GEMINI_API_KEY` está definida pero contiene un valor vacío al iniciarse el Sistema, THEN THE Sistema SHALL detener el inicio de la aplicación y registrar un mensaje de error en el log indicando que la variable de entorno requerida no puede estar vacía.
4. THE Sistema SHALL garantizar que el valor de `GEMINI_API_KEY` no aparezca en ningún archivo de código fuente, archivo de configuración versionado ni en el cuerpo de respuesta de ningún endpoint de la API.
5. WHEN el Sistema registre cualquier error relacionado con la Gemini_API, THE Sistema SHALL omitir el valor de `GEMINI_API_KEY` de la entrada de log, mostrando como máximo los primeros 4 caracteres seguidos de asteriscos para confirmar presencia sin exponer el valor completo.

---

### Requisito 7: Protección de Datos Personales Simulados

**Historia de Usuario:** Como Técnico o Encargada_Compras, quiero que el sistema use únicamente datos de clientes simulados, para cumplir con la Ley_29733 y proteger la privacidad.

#### Criterios de Aceptación

1. THE Sistema SHALL utilizar exclusivamente datos de clientes simulados, donde un dato simulado se define como un nombre que no corresponde a ninguna persona natural identificable y un número de documento que no corresponde a un DNI, RUC o pasaporte válido emitido por la RENIEC o SUNAT.
2. WHEN el Sistema procesa una solicitud a cualquier endpoint de la API, THE Sistema SHALL omitir de la respuesta cualquier campo que contenga un valor que supere la validación de formato de documento real (DNI de 8 dígitos válido según RENIEC, RUC de 11 dígitos válido según SUNAT) o un nombre que coincida con registros de personas naturales identificables.
3. WHERE el Sistema incluya datos iniciales de prueba (seed data), THE Sistema SHALL poblar la base de datos únicamente con registros ficticios, donde cada registro debe incluir un nombre con al menos un componente claramente ficticio (p. ej., prefijo "Test_", "Ficticio_" o similar) y un número de documento que no pase la validación de formato de documento real.
4. IF el Sistema detecta un intento de ingresar un dato de cliente que supera la validación de formato de documento real durante el registro o actualización, THEN THE Sistema SHALL rechazar la operación y devolver un mensaje de error indicando que no se permiten datos personales reales, sin persistir el dato en la base de datos.

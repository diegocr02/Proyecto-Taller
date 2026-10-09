# Implementation Plan: Gestión de Taller e Inventario — Jorge Motors

## Overview

Implementación incremental de la aplicación web sobre CodeIgniter 4 + MySQL 8 (XAMPP). El plan sigue el orden: infraestructura compartida → módulo OT → módulo Inventario → módulo Historial → integración final. Cada tarea produce código funcional que puede ejecutarse y probarse de forma aislada antes de pasar a la siguiente.

---

## Tasks

- [ ] 1. Configurar la estructura del proyecto CodeIgniter 4 y la infraestructura compartida
  - Crear la estructura de carpetas de los tres módulos bajo `app/Modules/{OT,Inventario,Historial}/Controllers/` y `app/Modules/{OT,Inventario,Historial}/Models/`.
  - Registrar los módulos en `app/Config/Autoload.php` o equivalente CI4 (namespaces PSR-4).
  - Crear `app/Config/ConfigEntorno.php`: leer `GEMINI_API_KEY` desde `.env`; lanzar excepción de arranque si está ausente o vacía; enmascarar el valor en logs (máx. 4 caracteres visibles + asteriscos).
  - Crear `.env.example` con `GEMINI_API_KEY=` y confirmar que `.env` está en `.gitignore`.
  - Instalar y configurar PHPUnit para pruebas unitarias (o verificar que CI4 lo incluya).
  - _Requisitos: R6.1, R6.2, R6.3, R6.4_

  - [ ] 1.1 Crear `ConfigEntorno` con lectura y enmascaramiento de `GEMINI_API_KEY`
    - Implementar la clase `app/Config/ConfigEntorno.php`.
    - _Requisitos: R6.1, R6.2, R6.3, R6.4, R6.5_

  - [ ]* 1.2 Escribir prueba unitaria para `ConfigEntorno`
    - Verificar arranque exitoso con clave presente y válida.
    - Verificar excepción cuando la clave está ausente.
    - Verificar excepción cuando la clave está vacía.
    - Verificar que el log muestra máx. 4 caracteres + asteriscos.
    - _Requisitos: R6.2, R6.3, R6.5_

- [ ] 2. Implementar `ValidadorEntrada` y su interfaz
  - Crear `app/Libraries/ValidadorEntrada.php` con los métodos:
    - `validarPlaca(string $placa): bool` — patrón LLL-NNN.
    - `validarCamposObligatorios(array $campos): void` — rechaza vacíos y solo-espacios.
    - `validarCantidadEnteraPositiva(mixed $cantidad): bool`.
    - `validarClienteSimulado(string $cliente): bool` — rechaza DNI (8 dígitos) y RUC (11 dígitos) con formato real.
    - `validarTerminoBusqueda(string $termino): bool` — 1–100 caracteres.
  - Todos los métodos lanzan o devuelven estructuras compatibles con la tabla de errores del diseño.
  - _Requisitos: R1.3, R1.4, R1.5, R1.8, R2.3, R3.5, R4.3, R4.4, R4.5, R7.2, R7.4_

  - [ ] 2.1 Crear `ValidadorEntrada` con todos sus métodos de validación
    - _Requisitos: R1.3, R1.4, R1.5, R1.8, R2.3, R3.5, R4.3, R4.4, R4.5, R7.2, R7.4_

  - [ ]* 2.2 Escribir prueba de propiedad para campos obligatorios vacíos / solo-espacios (Propiedad 2)
    - **Propiedad 2: Campos obligatorios vacíos o solo-espacios son rechazados sin persistencia**
    - **Valida: Requisitos R1.3, R1.4, R1.8, R4.3, R4.5**
    - Generar cadenas con valor vacío o compuesto únicamente de espacios y verificar rechazo.

  - [ ]* 2.3 Escribir prueba de propiedad para placa con formato inválido (Propiedad 3)
    - **Propiedad 3: Placa con formato inválido es rechazada en cualquier operación**
    - **Valida: Requisitos R1.5, R5.6**
    - Generar cadenas que no cumplan el patrón LLL-NNN y verificar rechazo con mensaje de formato.

  - [ ]* 2.4 Escribir prueba de propiedad para cantidad inválida en inventario (Propiedad 9)
    - **Propiedad 9: Cantidad no positiva o no entera es rechazada en cualquier operación de inventario**
    - **Valida: Requisitos R3.5, R4.4**
    - Generar valores ≤ 0 y no-enteros; verificar rechazo sin modificar datos.

  - [ ]* 2.5 Escribir prueba de propiedad para documento real en cliente simulado (Propiedad 15)
    - **Propiedad 15: Rechazo de datos de cliente con documento de formato real**
    - **Valida: Requisitos R7.2, R7.4**
    - Generar cadenas que superen la validación de formato DNI/RUC y verificar rechazo.

  - [ ]* 2.6 Escribir prueba unitaria para `ValidadorEntrada`
    - Cubrir casos válidos e inválidos de placa, campos vacíos, cantidades, términos de búsqueda y documentos de cliente.
    - _Requisitos: R1.3, R1.4, R1.5, R1.8, R2.3, R3.5, R4.3, R4.4, R4.5, R7.2, R7.4_

- [ ] 3. Punto de control — validaciones de infraestructura
  - Asegurarse de que todas las pruebas unitarias y de propiedad de los pasos 1 y 2 pasan. Consultar al usuario si surge alguna duda.

- [ ] 4. Implementar la capa de datos: migraciones y modelos base
  - Crear las migraciones CI4 para las tablas `ordenes_trabajo`, `repuestos` y `movimientos_inventario` según los esquemas del diseño.
  - Crear `app/Modules/OT/Models/ModeloOT.php`: INSERT y consulta por id/placa sobre `ordenes_trabajo`.
  - Crear `app/Modules/Inventario/Models/ModeloRepuesto.php`: lectura, creación y actualización de stock de `repuestos`; registro atómico (transacción MySQL) en `movimientos_inventario`.
  - Crear `app/Modules/Historial/Models/ModeloHistorial.php`: mapeo de resultados del MCP al dominio de la aplicación.
  - _Requisitos: R1.1, R1.6, R1.9, R3.1, R3.6, R4.1, R4.2, R4.6, R5.1, R5.2_

  - [ ] 4.1 Crear migraciones para `ordenes_trabajo`, `repuestos` y `movimientos_inventario`
    - _Requisitos: R1.1, R1.6, R3.1, R3.6, R4.1, R4.6_

  - [ ] 4.2 Implementar `ModeloOT`
    - Métodos: `crear(array $datos): int` (retorna Número_OT), `buscarPorId(int $id): ?array`, `buscarPorPlaca(string $placa): array`.
    - _Requisitos: R1.1, R1.6_

  - [ ]* 4.3 Escribir prueba de propiedad para unicidad de Número_OT (Propiedad 1)
    - **Propiedad 1: Creación de OT con datos válidos asigna Número_OT único**
    - **Valida: Requisitos R1.1, R1.6**
    - Insertar múltiples OTs con datos válidos y verificar que cada Número_OT es único y positivo.

  - [ ] 4.4 Implementar `ModeloRepuesto`
    - Métodos: `buscarPorCodigo(string $codigo): ?array`, `actualizarStock(string $codigo, int $delta, array $movimiento): void` (transacción), `crear(array $datos): void`.
    - _Requisitos: R3.1, R3.2, R3.3, R4.1, R4.2, R4.6_

  - [ ]* 4.5 Escribir prueba de propiedad para despacho válido reduce stock atómicamente (Propiedad 6)
    - **Propiedad 6: Despacho válido reduce el stock exactamente y persiste el movimiento de forma atómica**
    - **Valida: Requisitos R3.1, R3.6**
    - Generar stock S y cantidad C con C ≤ S; verificar stock final = S − C y movimiento persistido.

  - [ ]* 4.6 Escribir prueba de propiedad para despacho con C > S rechazado (Propiedad 7)
    - **Propiedad 7: Despacho con cantidad mayor al stock disponible es rechazado sin modificar datos**
    - **Valida: Requisitos R3.2**
    - Generar C > S; verificar stock sigue siendo S y no se crea movimiento.

  - [ ]* 4.7 Escribir prueba de propiedad para lote válido incrementa stock atómicamente (Propiedad 11)
    - **Propiedad 11: Lote válido incrementa el stock exactamente y persiste el movimiento de forma atómica**
    - **Valida: Requisitos R4.1, R4.6**
    - Generar stock S y lote L; verificar stock final = S + L y movimiento de ingreso persistido.

  - [ ]* 4.8 Escribir prueba de propiedad para lote con código nuevo crea repuesto (Propiedad 12)
    - **Propiedad 12: Lote con código inexistente crea el repuesto con stock inicial igual a la cantidad**
    - **Valida: Requisitos R4.2**
    - Generar código inexistente y cantidad L; verificar creación con stock = L y movimiento ingreso.

- [ ] 5. Punto de control — capa de datos
  - Ejecutar migraciones en MySQL XAMPP local. Asegurarse de que todas las pruebas de modelos pasan. Consultar al usuario si surge alguna duda.

- [ ] 6. Implementar el módulo OT (HU01)
  - Crear `app/Modules/OT/Controllers/ControladorOT.php`:
    - `POST /ot` — valida con `ValidadorEntrada`, persiste con `ModeloOT`, retorna `{"numero_ot": N}` HTTP 201.
    - Manejo de errores: HTTP 422 para validación, HTTP 503 si la base de datos no responde.
  - Registrar la ruta en `app/Config/Routes.php`.
  - _Requisitos: R1.1, R1.2, R1.3, R1.4, R1.5, R1.6, R1.7, R1.8, R1.9_

  - [ ] 6.1 Implementar `ControladorOT` con endpoint `POST /ot`
    - _Requisitos: R1.1, R1.2, R1.3, R1.4, R1.5, R1.6, R1.8, R1.9_

  - [ ]* 6.2 Escribir prueba unitaria para `ControladorOT`
    - Escenarios: datos válidos → HTTP 201 con Número_OT; placa vacía → HTTP 422; descripción vacía → HTTP 422; formato de placa inválido → HTTP 422; cliente vacío → HTTP 422; base de datos no disponible → HTTP 503.
    - _Requisitos: R1.1, R1.3, R1.4, R1.5, R1.8, R1.9_

- [ ] 7. Implementar la interfaz `ServicioConsultaInterface` y `ConectorMCP`
  - Crear `app/Libraries/ServicioConsultaInterface.php` con los métodos `buscarRepuestos` y `obtenerHistorialVehicular` según la firma del diseño.
  - Crear `app/Libraries/ConectorMCP.php` que implemente `ServicioConsultaInterface`:
    - Solo emite `GET` hacia el MCP externo.
    - Aplica timeout de 1,0 s; lanza excepción capturada como HTTP 503 en los controladores.
    - Los controladores inyectan `ServicioConsultaInterface`; nunca dependen de `ConectorMCP` directamente.
  - _Requisitos: R2.2, R2.4, R2.6, R5.4, R5.5_

  - [ ] 7.1 Crear `ServicioConsultaInterface` y `ConectorMCP`
    - _Requisitos: R2.2, R2.4, R2.6, R5.4, R5.5_

  - [ ]* 7.2 Escribir prueba de propiedad para que ConectorMCP solo emita HTTP GET (Propiedad 4)
    - **Propiedad 4: ConectorMCP solo emite operaciones HTTP GET**
    - **Valida: Requisitos R2.2, R2.6, R5.5**
    - Mockear el cliente HTTP e interceptar todas las llamadas; verificar que el método siempre es GET.

  - [ ]* 7.3 Escribir prueba de propiedad para rechazo de término de búsqueda inválido (Propiedad 5)
    - **Propiedad 5: Término de búsqueda inválido es rechazado sin llamar al MCP**
    - **Valida: Requisitos R2.3**
    - Generar términos vacíos o > 100 caracteres; verificar rechazo y cero llamadas al MCP.

  - [ ]* 7.4 Escribir prueba unitaria para `ConectorMCP`
    - Escenarios: respuesta HTTP 200 con datos correctos; timeout > 1 s (stub); error HTTP 4xx/5xx.
    - _Requisitos: R2.2, R2.4, R2.6, R5.4, R5.5_

- [ ] 8. Implementar el módulo Inventario (HU02, HU03, HU04)
  - Crear `app/Modules/Inventario/Controllers/ControladorInventario.php`:
    - `GET /inventario/repuestos?q={termino}` — delega en `ServicioConsultaInterface::buscarRepuestos`; valida término con `ValidadorEntrada`. _HU02_
    - `POST /inventario/despachos` — valida código, OT y cantidad; verifica stock, estado de OT, persiste dentro de transacción. _HU03_
    - `POST /inventario/lotes` — valida código, nombre (si nuevo) y cantidad; crea o incrementa stock, persiste movimiento de ingreso. _HU04_
    - Retorna `{"error": "descripción"}` con el código HTTP correspondiente según la tabla de errores del diseño.
  - Registrar las rutas en `app/Config/Routes.php`.
  - _Requisitos: R2.1, R2.3, R2.4, R2.5, R3.1–R3.7, R4.1–R4.6_

  - [ ] 8.1 Implementar `GET /inventario/repuestos` en `ControladorInventario` (HU02)
    - _Requisitos: R2.1, R2.3, R2.4, R2.5, R2.6_

  - [ ] 8.2 Implementar `POST /inventario/despachos` en `ControladorInventario` (HU03)
    - _Requisitos: R3.1, R3.2, R3.3, R3.4, R3.5, R3.6, R3.7_

  - [ ]* 8.3 Escribir prueba de propiedad para referencia inexistente rechazada sin modificar datos (Propiedad 8)
    - **Propiedad 8: Operación con referencia inexistente es rechazada sin modificar datos**
    - **Valida: Requisitos R3.3, R3.4**
    - Generar códigos y Números_OT que no existan; verificar rechazo y sin cambios en BD.

  - [ ]* 8.4 Escribir prueba de propiedad para despacho contra OT no abierta rechazado (Propiedad 10)
    - **Propiedad 10: Despacho contra OT en estado no abierto es rechazado sin modificar datos**
    - **Valida: Requisitos R3.7**
    - Generar OTs con estado `cerrada` o `cancelada`; verificar rechazo y stock sin modificar.

  - [ ] 8.5 Implementar `POST /inventario/lotes` en `ControladorInventario` (HU04)
    - _Requisitos: R4.1, R4.2, R4.3, R4.4, R4.5, R4.6_

  - [ ]* 8.6 Escribir prueba unitaria para `ControladorInventario`
    - Cubrir los escenarios de éxito y todos los errores de HU02, HU03 y HU04.
    - _Requisitos: R2.1–R2.6, R3.1–R3.7, R4.1–R4.6_

- [ ] 9. Punto de control — módulos OT e Inventario
  - Asegurarse de que todas las pruebas de los pasos 6, 7 y 8 pasan. Consultar al usuario si surge alguna duda.

- [ ] 10. Implementar el módulo Historial (HU05)
  - Crear `app/Modules/Historial/Controllers/ControladorHistorial.php`:
    - `GET /historial/{placa}` — valida placa con `ValidadorEntrada`; delega en `ServicioConsultaInterface::obtenerHistorialVehicular`; mapea resultado con `ModeloHistorial`.
    - Retorna lista de OTs (id_ot, fecha, descripcion, técnico) o lista vacía con mensaje; HTTP 503 si el MCP no responde.
  - Crear `app/Modules/Historial/Models/ModeloHistorial.php`: mapeo del array MCP al dominio.
  - Registrar la ruta en `app/Config/Routes.php`.
  - _Requisitos: R5.1, R5.2, R5.3, R5.4, R5.5, R5.6_

  - [ ] 10.1 Implementar `ModeloHistorial` con mapeo de respuesta MCP
    - _Requisitos: R5.1, R5.2_

  - [ ] 10.2 Implementar `ControladorHistorial` con endpoint `GET /historial/{placa}`
    - _Requisitos: R5.1, R5.2, R5.3, R5.4, R5.5, R5.6_

  - [ ]* 10.3 Escribir prueba de propiedad para historial con N registros completos (Propiedad 13)
    - **Propiedad 13: Historial vehicular devuelve exactamente todos los registros de la placa**
    - **Valida: Requisitos R5.1, R5.2**
    - Stubear MCP con N OTs para una placa; verificar que la respuesta contiene exactamente N registros con los cuatro campos requeridos.

  - [ ]* 10.4 Escribir prueba unitaria para `ControladorHistorial`
    - Escenarios: placa válida con resultados, placa válida sin resultados, placa inválida (formato), MCP no disponible.
    - _Requisitos: R5.1–R5.6_

- [ ] 11. Implementar protección y enmascaramiento de `GEMINI_API_KEY` en logs
  - Integrar `ConfigEntorno` en el flujo de arranque de CI4 (`app/Config/Boot.php` o `index.php`) para que la aplicación no inicie si la clave está ausente o vacía.
  - Verificar que ningún `catch` de error relacionado con Gemini expone el valor de la clave en los logs.
  - _Requisitos: R6.1, R6.2, R6.3, R6.4, R6.5_

  - [ ] 11.1 Integrar `ConfigEntorno` en el arranque de la aplicación CI4
    - _Requisitos: R6.1, R6.2, R6.3, R6.4_

  - [ ]* 11.2 Escribir prueba de propiedad para enmascaramiento de `GEMINI_API_KEY` en logs (Propiedad 14)
    - **Propiedad 14: Enmascaramiento de GEMINI_API_KEY en logs de error**
    - **Valida: Requisitos R6.5**
    - Generar claves de distintas longitudes (≥ 5 chars); verificar que el log contiene máx. 4 caracteres visibles seguidos de asteriscos y nunca la clave completa.

- [ ] 12. Poblar seed data con datos ficticios y validar política R7
  - Crear un seeder CI4 (`app/Database/Seeds/SeedDatosFicticios.php`) que inserte OTs y repuestos de prueba usando nombres con prefijo `Test_` o `Ficticio_` y números de documento que no superen la validación de formato real.
  - Verificar que el seed NO inserta ningún registro que pase la validación de DNI/RUC real.
  - _Requisitos: R7.1, R7.3_

  - [ ] 12.1 Crear `SeedDatosFicticios` con datos de cliente simulados
    - _Requisitos: R7.1, R7.3_

  - [ ]* 12.2 Escribir prueba unitaria que verifica que el seed data no contiene documentos reales
    - Iterar todos los registros del seed y afirmar que ninguno pasa la validación de formato DNI/RUC real.
    - _Requisitos: R7.1, R7.3_

- [ ] 13. Punto de control final — integración completa
  - Ejecutar la suite completa de pruebas (unitarias + propiedades + humo).
  - Correr las migraciones y el seeder en MySQL XAMPP local y verificar el flujo OT → Despacho → Stock.
  - Asegurarse de que todas las pruebas pasan. Consultar al usuario si surge alguna duda.

---

## Notes

- Las tareas marcadas con `*` son opcionales y pueden omitirse para una entrega MVP más rápida; cubren las 15 propiedades de corrección definidas en el diseño.
- Cada tarea referencia los requisitos específicos para trazabilidad completa.
- Las pruebas de propiedad (PBT) usan mocks/stubs para la base de datos y el MCP; la librería concreta queda por definir en ADR-003.
- Cada prueba PBT debe ejecutar mínimo 100 iteraciones e incluir el comentario de trazabilidad:
  `// Feature: gestion-taller-inventario, Propiedad N: <texto>`
- El campo `GEMINI_API_KEY` nunca debe aparecer en el código fuente ni en archivos versionados; solo en `.env` (fuera del repositorio).
- El `ConectorMCP` es el único punto de contacto con el MCP externo; los controladores solo dependen de `ServicioConsultaInterface`.

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "4.1"] },
    { "id": 1, "tasks": ["1.2", "2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "2.5", "2.6", "4.2"] },
    { "id": 3, "tasks": ["4.3", "4.4"] },
    { "id": 4, "tasks": ["4.5", "4.6", "4.7", "4.8", "6.1", "7.1"] },
    { "id": 5, "tasks": ["6.2", "7.2", "7.3", "7.4"] },
    { "id": 6, "tasks": ["8.1", "8.2", "8.5", "10.1"] },
    { "id": 7, "tasks": ["8.3", "8.4", "8.6", "10.2"] },
    { "id": 8, "tasks": ["10.3", "10.4", "11.1", "12.1"] },
    { "id": 9, "tasks": ["11.2", "12.2"] }
  ]
}
```

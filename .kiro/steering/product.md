# Producto · Sistema de Gestión de Taller y Repuestos Jorge Motors · Redacta todos los documentos en español.

> Versión 2.0 (2026-11-27). Documento obtenido por ingeniería inversa del código y de la base `data/taller.db`: describe el sistema tal como existe hoy. La versión anterior está en `.kiro/_historial/kiro_2026-11-27/steering/product.md`.

## Propósito
Digitalizar el registro de Órdenes de Trabajo (OT) y el control de inventario de repuestos de Jorge Motors, reemplazando el cuaderno y el Excel para reducir los descuadres de stock y las demoras en la atención al cliente, y ofrecer al personal un asistente de inteligencia artificial que responda preguntas sobre esos datos.

## Usuarios
El usuario elige su rol en un selector de la cabecera, sin autenticación (deuda técnica aceptada en ADR-002). Cada rol ve solo sus pestañas (`PANTALLAS_POR_ROL` en `frontend/static/app.js`):

| Rol | Descripción | Pestañas visibles |
|---|---|---|
| Recepcionista | Asesor de servicio; registra las OT | Registrar OT, Historial, Asistente IA |
| Técnico | Mecánico (Luis Pachas, Luis Luna, Miguel Torres); consulta historial y stock | Historial, Inventario, Asistente IA |
| Encargado_Compras | Encargado de Compras/Almacén; vigila el stock mínimo y compara el inventario físico | Inventario, Alertas, Comparación, Asistente IA |
| Gerente | Administración; revisa el desempeño por técnico | Las siete pestañas |

## Lo que hace (DENTRO)
1. Registro digital de OT. Si el cliente o el vehículo ya existen, se actualizan sus datos; si no, se crean (H-01).
2. Consulta del detalle de una OT por su identificador (H-01).
3. Consulta del historial de OT por placa o DNI, con hasta 100 resultados (H-02).
4. Consulta de stock de repuestos por código exacto o por parte del nombre, en solo lectura (H-03).
5. Alertas de stock mínimo (cantidad ≤ stock mínimo), con un contador en la pestaña y en la campana (H-04).
6. Comparación del conteo físico con el sistema; cada comparación se guarda en `comparaciones_conteo` (H-05).
7. Reporte de OT por técnico en un rango de fechas, exportable a CSV (H-06).
8. Indicador de carga a los 2 s y corte a los 30 s con opción de reintentar (H-07).
9. Protección de claves y uso exclusivo de datos simulados (H-08).
10. Asistente de IA JorgeBot: chat que responde en lenguaje natural con 7 herramientas MCP de solo lectura. Recuerda la conversación, muestra qué herramienta usó, guarda las conversaciones en el navegador y registra cada consulta en `trazabilidad_ia` (H-09).
11. Copia opcional de la base a MySQL de XAMPP para revisarla en phpMyAdmin (`data/exportar_a_xampp.py`); la app no la usa (H-08).

## Lo que NO hace (FUERA)
- Facturación electrónica integrada a SUNAT
- Módulo de pagos en línea
- App móvil para clientes
- Compra automática a proveedores
- Modificar el stock: ningún endpoint ni herramienta MCP lo actualiza (comprobado: no hay `INSERT`, `UPDATE` ni `DELETE` sobre `stock` en `app/` ni en `agente/`)
- Cambiar el estado de una OT o cerrarla: no existe ningún endpoint para hacerlo; las OT se crean con estado «abierta»
- Autenticación de usuarios

## Reglas no negociables (restricciones)
- Cumplimiento de la Ley N.° 29733 (Protección de Datos Personales): solo se almacenan y procesan datos simulados. Los clientes tienen nombres inventados y DNI `100000xx`, y el agente no revela nombres ni DNI de clientes.
- El agente se presenta como inteligencia artificial al saludar (regla 8 de `agente/instrucciones.txt`).
- El Servidor MCP es exclusivamente de solo lectura: abre la base con `mode=ro` y no tiene herramientas de escritura.
- Entrega limitada al semestre en curso.

---

## Historial de cambios

| Fecha | Hallazgo que lo origina | Cambio realizado |
|---|---|---|
| 2026-09-25 | Auditoría Fase 1: "Recepcionista" ausente en lista de usuarios pese a ser el actor principal en requirements.md | Recepcionista añadido con su descripción de rol |
| 2026-09-25 | Auditoría Fase 1: "actualización de stock" en DENTRO contradice el modelo de solo lectura del MCP (requirements.md, ADR-002) | Reemplazado por "Consulta de stock" con nota PENDIENTE para que el equipo decida |
| 2026-11-27 | Ingeniería inversa: el asistente de IA (H-09) no figuraba en DENTRO; el código confirma que el stock es de solo lectura | Asistente de IA y exportación CSV añadidos a DENTRO; nota PENDIENTE marcada como resuelta |
| 2026-11-27 | Ingeniería inversa, versión 2.0: faltaban las pestañas por rol, el detalle de OT, el contador de alertas, la copia a XAMPP y lo que el sistema no hace (cambiar el estado de las OT, autenticación) | Documento reescrito con el alcance real numerado y referencias a cada historia |

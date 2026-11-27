# Producto · Sistema de Gestión de Inventario Jorge Motors · Redacta todos los documentos en español.

## Propósito
Digitalizar el registro de Órdenes de Trabajo y el control de inventario de repuestos de Jorge Motors, reemplazando el cuaderno y Excel para reducir descuadres de stock y demoras en la atención al cliente.

## Usuarios
- Recepcionista / asesor de servicio (usuario principal; registra y gestiona las OT)
- Técnico mecánico (consulta historial y stock para ejecutar reparaciones)
- Encargado de Compras/Almacén (gestiona alertas de stock mínimo y compara inventario físico)
- Gerente/Administración (genera reportes de desempeño por técnico)

## Lo que hace (DENTRO)
- Registro digital de Orden de Trabajo (OT)
- Consulta de historial de cliente y vehículo
- Consulta de stock de repuestos (solo lectura a través del Servidor MCP)
- Generación de alertas de stock mínimo
- Comparación de conteo físico con el registro del sistema
- Generación de reporte de OT por técnico (con exportación a CSV)
- Asistente de IA (JorgeBot) que responde preguntas del taller consultando la base de datos con herramientas MCP de solo lectura, con trazabilidad de cada consulta

> **Resuelto (2026-11-27, ingeniería inversa):** la versión original de este documento decía «consulta y **actualización** de stock». El sistema construido trata el stock como **solo lectura**: ningún endpoint ni herramienta MCP lo modifica. Si en el futuro se necesita actualizar el stock, hay que abrir un nuevo requisito funcional y revisar el ADR-002.

## Lo que NO hace (FUERA)
- Facturación electrónica integrada a SUNAT
- Módulo de pagos en línea
- App móvil para clientes
- Compra automática a proveedores

## Reglas no negociables (restricciones)
- Cumplimiento de la Ley N.° 29733 (Protección de Datos Personales): solo se almacenan y procesan datos simulados; ningún dato personal real se almacena ni expone
- Entrega limitada al semestre en curso (restricción de tiempo)
- El Servidor MCP de la semana 4 se usa en modo exclusivo de solo lectura; no se amplía con herramientas de escritura

---

## Historial de cambios

| Fecha | Hallazgo que lo origina | Cambio realizado |
|---|---|---|
| 2026-09-25 | Auditoría Fase 1: "Recepcionista" ausente en lista de usuarios pese a ser el actor principal en requirements.md | Recepcionista añadido con su descripción de rol |
| 2026-09-25 | Auditoría Fase 1: "actualización de stock" en DENTRO contradice el modelo de solo lectura del MCP (requirements.md, ADR-002) | Reemplazado por "Consulta de stock" con nota PENDIENTE para que el equipo decida |
| 2026-11-27 | Ingeniería inversa: el asistente de IA (H-09) no figuraba en DENTRO; el código confirma que el stock es de solo lectura | Asistente de IA y exportación CSV añadidos a DENTRO; nota PENDIENTE marcada como resuelta |

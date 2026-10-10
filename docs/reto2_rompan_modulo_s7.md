# Reto 2 · Rompan su módulo — `GET /ordenes/{id_ot}` [H-01]

Fecha: 2026-10-10. Base de datos: copia de `data/taller.db` con los datos simulados de `data/seed.py`.

Antes de la sesión, `id_ot` estaba declarado como `int`: cualquier valor no numérico respondía **422**, no 404 como pide la guía. Se cambió a texto validado (`isascii()`, `isdigit()`, máximo 9 dígitos) y todo lo demás responde 404.

| Entrada | Resultado | ¿Correcto? |
|---|---|---|
| `1` (existe) | 200 con «Mantenimiento preventivo 45k» | Sí |
| `9999` (no existe) | 404 «Orden de trabajo no encontrada» | Sí |
| `no-existe-zz` | 404 (antes: 422) | Sí, corregido |
| `-1` | 404 (antes: 422) | Sí, corregido |
| `'` (comilla simple) | 404; no llega a la consulta SQL | Sí |
| `%20` (espacio) | 404 | Sí |
| vacío (`/ordenes/`) | 307, redirige a `/ordenes`, que solo acepta POST (405) | Aceptable: es otra ruta |
| 500 caracteres `1…1` | 404; no se convierte a entero gigante | Sí |
| `1 OR 1=1` | 404; la consulta es parametrizada | Sí |

Prueba automatizada: `tests/test_ordenes_detalle.py::test_entradas_inesperadas_responden_404`.

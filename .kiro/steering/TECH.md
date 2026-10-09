# Stack y reglas técnicas
- Framework: Se adopta CodeIgniter 4 en su versión estable vigente, con un módulo por dominio., versión estable vigente [VERIFICAR].
- Base de datos: MySQL/MariaDB de XAMPP; collation utf8mb4_unicode_ci.
- Servidor: Apache de XAMPP; raíz pública: [CARPETA PUBLIC DEL FRAMEWORK].
- Nombres: español; snake_case en base de datos; PascalCase en clases; kebab-case en rutas.
- Secretos únicamente en .env; .env nunca se versiona.
- Todo módulo nuevo traza a una historia de requirements.md; si no traza, no se construye.
- FRONTERA: no implementar agente conversacional, modelos de IA ni MCP hasta la Unidad 3. Dejar solo el punto de extensión documentado.
- Toda tabla nueva obliga a actualizar docs/arquitectura/modelo_datos.md en el mismo commit.
---
 
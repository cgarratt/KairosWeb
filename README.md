# KairosWeb v2.0.10 — Release compacto para GitHub

Este paquete acumula **v2.0.9** y refuerza Configuración → Pivotes: la actualización automática MCP **solo modifica PROPUESTO**. Los anclajes VALIDADO / CONFIRMADO conservan precio, fecha y estado, incluso si MCP devuelve resultados diferentes. Una validación técnica MCP no publica ni confirma por sí misma.

**VIRTUAL:** la semana flash crash del 06–12/10/2025 queda excluida de la selección automática del CL exploratorio; no se selecciona arbitrariamente otro mínimo ni se sobrescribe el Master. Los toques históricos post-O1 no equivalen a cercanía actual ni fills.

Se conservan los módulos de Órdenes Fase 1, Compras, Ventas, Balancer, Forecast, Configuración y Alertas. Órdenes sigue siendo **SOLO PROPUESTAS**; ningún envío/cancelación a exchanges, conciliación de fills o cambio de custodia.

## Despliegue
1. Subir **el contenido descomprimido** a la raíz del mismo repositorio, conservando las carpetas. No subir el ZIP como código sin descomprimir.
2. Comprueba en Render: `/health` → versión **2.0.10**, estado **UP**, `release_assets.consistent: true`.
3. En Configuración/Pivotes prueba que MCP respeta los VALIDADOS y CONFIRMADOS; revisa Compras y Órdenes.
4. Para escribir/publicar en el Master se necesita autenticación administrativa, validación y aprobación; **no usar una prueba de lectura para cambiar estados**.

Ver `RELEASE_NOTES_v2.0.10.md` para alcance, cautelas y controles. El esquema del Master permanece **5.0.0**.

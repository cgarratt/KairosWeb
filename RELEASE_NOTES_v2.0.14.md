# Release Notes · KairosWeb v2.0.14

Fecha de construcción: 2026-10-19. Base 2.0.13.

- Compras: Matriz Fibonacci P1/P2, 4 pesos **post compra** y toques históricos diarios **post P2**; precio Fibo sin semáforo de deriva. Mantiene equilibrio secuencial y QF.
- Ventas: objetivo monetario USDT junto con porcentaje.
- Forecast: tabla «Simulación - Ondas Elliott» sin columna Estado, sin alterar bloqueo de VALIDADO/CONFIRMADO.
- Órdenes: listado unificado con vistas KairosGPT, filtros combinables, semáforos de proximidad, contador y limpieza; todas las filas siguen siendo **no colocadas**.
- Mantiene `schema_version=5.0.0`, fuentes Sheets/MCP, BTC NEVER SELL y fase 1 no operativa.

Validación local: `python -m pytest -q` (157 aprobadas, 2 omitidas); `node tests/*.js`, `node --check static/*.js`, `python -m compileall -q .`; parseo Jinja 13 plantillas; prueba Chromium de vistas combinables. No se han probado credenciales ni despliegue Render HTTP en este release.

Comprobación: `/health` => `2.0.14`, `UP`, `release_assets.consistent=true` una vez desplegado.

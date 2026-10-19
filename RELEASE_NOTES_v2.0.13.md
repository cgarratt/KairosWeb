# KairosWeb 2.0.13 — Forecast con pivotes VALIDADO/CONFIRMADO fijos

**Base:** KairosWeb v2.0.12. **Ámbito:** código KairosWeb solamente; no cambia KairosGPT, Master ni datos publicados.

## Contrato del cambio

- `forecast_fibo_plan.js`: `wavePath()` inmoviliza CL y O1–O5 con estados VALIDADO/CONFIRMADO usando precios del Master, ignora cambios de los selectores para esos pivotes y sigue calculando solo PROPUESTO.
- `templates/forecast.html`: gráfica SVG, tabla de ondas y proyecciones comparten `wavePath()`. Marcas con candado, estado y color ámbar/verde para los pivotes protegidos; PROPUESTO continúa como escenario.
- `app.py`: la carga de Forecast suministra precio, fecha y estado de CL/O1–O5 desde el `07_PIVOTES` publicado. `/health` añade comprobaciones de los componentes Forecast.
- Las estructuras incompatibles o sin precio publicado se marcan sin sobrescribir el Master.
- No se habilita ejecución de órdenes ni alteración de custodia, pivotes o reservas.

## Compatibilidad y precauciones

- Módulos anteriores y el esquema Sheets 5.0.0 no cambian. Compras usa P1/P2 para simulaciones y respeta INFRA/QF; Ventas ordinarias no hereda el filtro.
- Un pivote propuesto sigue siendo simulación provisional. La publicación de estados se realiza exclusivamente desde Configuración → Pivotes con autorización.
- El despliegue no debe inferir que una simulación implica confirmación de pivote o fill.

## Verificación

- `python -m pytest -q`, pruebas Node de `tests/*.js`, `python -m compileall -q`, `node --check` y parseo de Jinja2.
- `/health` debe responder `version=2.0.13` y `release_assets.consistent=true` una vez desplegado. Integración con Render, MCP y Sheets se valida por separado.
- Manifest `RELEASE_MANIFEST_v2.0.13.json` y `SHA256SUMS.txt` permiten auditar la integridad; los valores SHA se calculan sobre bytes exactos del paquete.

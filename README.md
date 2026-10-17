# KairosWeb v1.6.0

Release de KairosWeb basado en v1.5.0 con las mejoras 26–33 de nomenclatura, parámetros y Forecast.

**Leer primero:** [RELEASE_NOTES_v1.6.0.md](RELEASE_NOTES_v1.6.0.md) y [MIGRACION_NOMENCLATURA_FIB_v1.6.0.md](MIGRACION_NOMENCLATURA_FIB_v1.6.0.md).

Desplegar el contenido del ZIP **descomprimido** en la raíz del repo GitHub, usando las variables secretas existentes en Render.

Google Sheets `KAIROS_V5_MASTER` (schema 5.0.0) es la fuente operativa. Binance/Hyperliquid MCP suministran mercado; no hay respaldo de snapshots JSON. El ZIP no publica cambios en el Master ni ejecuta órdenes.

Pruebas: `PYTHONPATH=.:tests pytest -q` y los scripts JS de `tests/` (requieren Node.js). Para pruebas visuales offline con Chromium, revisar los scripts browser en `tests/`.

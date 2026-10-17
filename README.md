# KairosWeb v1.7.0

Release basado en v1.6.0, incorporando las mejoras **34 y 35**:
orden canónico de parámetros Fibonacci en Configuración y encabezados abreviados en Forecast.

Leer primero [RELEASE_NOTES_v1.7.0.md](RELEASE_NOTES_v1.7.0.md). Se preservan [RELEASE_NOTES_v1.6.0.md](RELEASE_NOTES_v1.6.0.md) y el mapa de migración para compatibilidad histórica.

Descomprimir y subir el contenido del ZIP a la raíz del repo GitHub. El despliegue requiere la configuración existente de Render; el ZIP **no despliega, no publica Google Sheets y no envía órdenes**. El esquema del Master continúa en 5.0.0.

Pruebas offline: `PYTHONPATH=.:tests pytest -q`; JS: `node tests/test_forecast_fibo_v14.js`, `node tests/test_forecast_segments.js`, `node tests/test_settings_format.js`; visuales con Playwright/Chromium si el entorno lo permite.

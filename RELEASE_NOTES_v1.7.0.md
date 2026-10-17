# KairosWeb v1.7.0 — orden Fibonacci y cabeceras simplificadas

## Mejoras incluidas

- **34 · Orden de tramos en Settings:** O2C1 (38.2%), O2C2 (50%), O2C3 (61.8%), O2C4 (78.6%); orden equivalente O4C1–C4. Extensiones O3V1–V4 y O5V1–V4 en orden 1.618, 2.618, 3.618, 4.618. La clasificación solo cambia el orden visual: cada input conserva su índice y clave originales del Master para guardar cambios auditados sin cruce de porcentajes.
- **35 · Cabecera de tabla Forecast O2 abreviada:** `Token | Precio 38.2% | USDT | Precio 50% | USDT | Precio 61.8% | USDT | Precio 78.6% | USDT | Total USDT`. La nomenclatura O2C1–O2C4 permanece en el atributo `title` para contexto/auditoría.
- **Forecast solo local:** cambiar los cuatro porcentajes de O2, O3, O4, O5 recalcula la simulación en navegador; no envía POST ni guarda nada en Google Sheets. Los parámetros oficiales solo se guardan desde **Configuración → Guardar cambios**, con autorización y auditoría.

## Sin cambios

- No modificar valores de reparto, órdenes, fills, indicadores ni cálculos financieros.
- Mismo Master nativo, `schema_version=5.0.0`, claves históricas de compatibilidad y fuente MCP.
- Nada modifica el Master por instalar ZIP. No hay deploy automático en Render.
- BTC NEVER SELL, HODL protegido, Quantfury y bloqueos de pivotes/BSI se mantienen.

## Verificación post-despliegue

1. `GET /health` debe indicar versión `1.7.0`.
2. Settings: en Compras O2 y O4, Fib 61.8 aparece ANTES de Fib 78.6. No cambian porcentajes.
3. Forecast: tabla encabezada solo Precio 38.2% / USDT / ... / Total USDT.
4. Cambiar porcentajes dentro de Forecast modifica tablas locales y vuelve al valor del Master tras recargar, sin escribir Google Sheets.
5. Si `DATA ERROR`, revisar `GET /api/sheets-status` y logs antes de hacer ajustes en el Master.

# KairosWeb v1.6.0 — Forecast, nomenclatura y parámetros

**Base:** KairosWeb v1.5.0. **Alcance:** mejoras 26–33 aprobadas. **Versión de contrato Google Sheets:** 5.0.0, sin cambios.

## Cambios implementados

1. Renombramiento canónico O2C1–O2C4, O3V1–O3V4, O4C1–O4C4 y O5V1–O5V4 en Forecast, controles, Settings y resúmenes de Compras. Correspondencia histórica Fib 50/61.8 preservada. Ver [MIGRACION_NOMENCLATURA_FIB_v1.6.0.md](MIGRACION_NOMENCLATURA_FIB_v1.6.0.md).
2. Se retiran de los **parámetros editables de KairosWeb** las antiguas bolsas C1 15% P y C2 10% P, que **no se añaden** al presupuesto de compras 25% P por onda. Los valores históricos se conservan en el Master original.
3. Meta USDT unificada: `STRUCTURAL_USDT_TARGET` es el único valor activo en KairosWeb, leído por Portafolio, Balancer, Ventas y O3. `ORDINARY_DEFAULT_USDT_TARGET` permanece histórico; O5 no se detiene por la meta 40%.
4. Sección Settings → Parámetros → Portafolio contiene exactamente **Objetivo estructural de liquidez** y **Tolerancia de desvío del Balancer**. Los otros parámetros conservan grupos de O2/O3/O4/O5, Trading QF, BSI y Alertas.
5. Forecast O2 muestra exclusivamente slider de 0–25% P, porcentaje seleccionado y **USDT simulado a su derecha**. Una advertencia compacta conserva la información sobre caja insuficiente/QF.
6. La tabla de compras O2 etiqueta precio y USDT por O2C1, O2C2, O2C3 y O2C4. Las tablas de compras y los controles de Forecast mantienen distribución total 100% por onda.
7. **«Ondas y precios pivote · Cycle Low a O5» aparece inmediatamente después del gráfico «Trayectoria hipotética»**; ambos calculan a partir de los mismos selectores.
8. Modo Compras ahora visualiza las **cuatro** asignaciones O2C1–O2C4, consumiendo la misma distribución aprobada/simulada que Forecast.

## Seguridad e integridad

- **No** se modificó `KAIROS_V5_MASTER` ni se publicaron snapshots al generar este paquete.
- Datos de posiciones, costos, liquidez y parámetros: solo `KAIROS_V5_MASTER` PUBLICADO; MCP Binance y Hyperliquid para mercado. Sin fallback a JSON/local.
- Las simulaciones no son órdenes. BTC NEVER SELL; QF/HODL/Core protegidos según onda. BSI SELL bloqueado, TradingBot WATCH hasta certificación.
- Google Sheets conserva columnas C1/C2 históricas para no reinterpretar órdenes. La equivalencia se aplica explícitamente en la interfaz; no se escriben renombres automáticos en el libro remoto.
- Reglas O3/O5 y reparto aprobado O5 30% BTC/70% USDT no cambiados.

## Verificación antes y después del despliegue

1. Ejecutar `pytest -q` en el repo (dependencias de `requirements.txt`); pruebas JS con `node tests/test_forecast_fibo_v14.js`, `node tests/test_forecast_segments.js`, `node tests/test_settings_format.js`. Chromium opcional: `python tests/browser_forecast_v14.py`, `python tests/browser_settings_v15.py`.
2. En GitHub reemplazar el contenido del repositorio con los archivos **descomprimidos**. No subir claves ni snapshots JSON antiguos.
3. Confirmar `/health` devuelve `version: 1.6.0`; `/api/sheets-status` responde `OK` con último snapshot `PUBLICADO`.
4. En Settings → Parámetros, comprobar que Portafolio tenga solo dos campos y que los cuatro grupos Fibonacci sigan sumando 100%. **No guardar cambios de prueba en el Master real sin autorización.**
5. En Forecast comprobar labels por onda, slider compactado y tabla de ondas inmediatamente después de la trayectoria. Confirmar que un cambio simulado afecta tablas y distribución sin actualizar el Master.

**Estado:** pruebas locales finalizadas. Integración y comportamiento de producción en Render aún no comprobados.

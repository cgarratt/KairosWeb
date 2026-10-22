# KairosWeb v2.0.35 — Distribución actual del capital

## Cambio de Portafolio

Se reemplaza el donut histórico por la distribución actual entre **HODL + Core, Exchange, Liquidez operativa y ReservaTrading QF**. Los porcentajes e importes se calculan a precios Binance Spot del mismo análisis, con unidades/custodia de `02_POSICIONES` y liquidez de `03_LIQUIDEZ` del último MASTER PUBLICADO.

- HODL/Core = suma de unidades protegidas de 12 tokens × Spot correspondiente.
- Exchange = suma de unidades Exchange de 12 tokens × Spot correspondiente.
- Liquidez operativa = USDT físico − QF real.
- ReservaTrading QF = saldo Quantfury, ya incluido en USDT físico.
- Patrimonio = HODL/Core + Exchange + liquidez operativa + QF. La valoración debe cuadrar con el donut “Allocation por token” y con los KPI, con tolerancia de redondeo al centavo.

`08_INTEGRAL` permanece en el MASTER como fuente contable histórica, sin utilizarse en este gráfico. Las pérdidas realizadas no son activos y no forman parte del patrimonio actual. No se modifica la estrategia, los saldos, los movimientos ni los fills.

## Controles de integridad

- Verificar 12 activos; unidades HODL + Core + Exchange = unidades totales publicadas por token.
- Rechazar valores no finitos, cotización faltante, QF negativa o mayor que USDT físico, o discrepancia entre sumas de los dos donuts.
- Ante fallos, `N/D` y diagnóstico; nunca recalcular con cifras históricas o screenshots.
- `/health`: `version=2.0.35`, `release_assets.consistent=true` y `current_capital_donut_v2035.markers_ok=true`.

## Pruebas locales

- Python: 217 aprobadas, 2 omitidas.
- JavaScript: 9 suites aprobadas.
- Jinja: 12 plantillas analizadas.
- Integridad SHA256 del ZIP verificada después del empaquetado.
- Render HTTP y despliegue GitHub: **no realizados**.

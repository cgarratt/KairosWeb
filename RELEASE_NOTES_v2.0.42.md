# KairosWeb v2.0.42 — Hotfix de ledger y conciliación de fills agregados

**Problema reproducido:** `DATA ERROR · Google Sheets` en v2.0.41 al leer órdenes BUY completadas e incorporadas en el snapshot, cuyos registros `05_ORDENES` usan `CONCILIADO · 06_FILLS filaN` y `06_FILLS` conserva evidencia agregada por orden, sin Trade IDs individuales o tiempo UTC certificado.

**Corrección:** admitir ese formato solo si hay vínculo explícito con una orden `FILLED/COMPLETED`, fuente documentada en ambas hojas, token/lado/qty/fee consistentes, marcador único `ORDER_AGGREGATE_NO_TRADE_IDS`, conciliación confirmada y ausencia de duplicados. Una confirmación agregada no crea Trade ID ni timestamp real. Se mantiene `DATA ERROR` para registros abiertos, mezclas incompatibles o datos no conciliados.

**Diagnóstico:** el aviso del Dashboard incluye categoría de error segura además del ID, para localizar registros fallidos en Render sin exponer claves o saldos internos.

**Fuentes y seguridad:** no se modifica ni se escribe el MASTER; no se infieren fills; no se reprocesan saldos/tenencias; siguen BTC NEVER SELL, QF protegida y simulaciones sin órdenes.

**Pruebas locales:** 245 Python aprobadas, 2 omitidas, 4 subtests y 9 suites JavaScript. Flask/FastMCP y prueba HTTP de producción no disponibles en este entorno.

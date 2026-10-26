# KairosWeb v2.0.47 — Órdenes recomendadas

- Una sola tabla: propuestas por token y órdenes registradas en 26_ORDENES_GESTION.
- Filtros Exchange, Tier, BUY/SELL, Token, Nivel y Estado.
- PROPUESTA: no compromete fondos; CONFIRMADA: reserva el importe/unidades del venue; PARCIAL/EJECUTADA: registra evidencia sin acreditar inventario hasta conciliación 05/06 y snapshot.
- Confirmación directa de recomendación: escribe PROPUESTA + CONFIRMADA en una única petición batchUpdate de Sheets; si falla, no se da por confirmada.
- Conserva BTC NEVER SELL, QF protegida, moneda HYPE/USDC segregada, límites de Exchange/Tier y autorización administrativa/CSRF.
- Las 14 órdenes anteriores en 05_ORDENES siguen siendo fuente de compromisos; NO se importan ni duplican automáticamente en 26.
- Compras, Ventas y Forecast consumen la misma contabilidad de compromisos publicada; una ejecución no cambia posiciones ni caja hasta conciliación certificada.
- Ninguna orden se envía o modifica en exchanges.
- Requiere validación end-to-end en Render con cuenta administrativa y MASTER original.

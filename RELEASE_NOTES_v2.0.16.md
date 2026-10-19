# KairosWeb v2.0.16 — Notas de versión

## Alcance

Release de interfaz y simulación sobre v2.0.15, sin cambios de política financiera vigente ni de schema Sheets 5.0.0.

### Compras

- Introduce porcentajes C1/38.2%, C2/50%, C3/61.8%, C4/78.6% modificables exclusivamente para la simulación local.
- Autoajuste proporcional de los otros porcentajes, suma exacta de 100.00%, restauración de porcentajes O2/O4 publicados en Master.
- Actualiza matriz y gráficos inferiores con los mismos escenarios y conserva los controles de balanceo, déficit INFRA, QF y cantidades pendientes.

### Órdenes

- Incluye USDT compra y unidades venta en resumen por token.
- Incluye filtro Nivel en el backlog junto con Exchange, Tier, Operación y Token.
- Mejoras de cálculo de tamaños para propuestas Balance y Estructura: no exceder déficit, target o Exchange libre; tamaños de venta estructural sin política aprobada quedan por definir.

### Compatibilidad y cautelas

- Modo Órdenes permanece **fase 1: read-only, sin place/cancel/fills**.
- Ajustar porcentajes en Compras **no modifica** el Master ni las propuestas generadas por Órdenes con los pesos oficiales publicados; son escenarios separados.
- HYPE usa Hyperliquid Spot HYPE/USDC para pivotes macro semanales; no se mezcla con Binance Spot HYPEUSDT.
- Se requiere comprobar Render, `/health` y MCP en producción; no se declara certificación remota.

Ver `README.md` para instalación y lista de comprobación.

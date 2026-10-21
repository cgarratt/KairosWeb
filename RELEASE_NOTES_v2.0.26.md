# KairosWeb v2.0.26 — Integridad matemática y homologación

**Base:** v2.0.25. **Master:** KAIROS_V5_MASTER schema 5.0.0. **No toca inventario ni envía órdenes.**

- Balancer BUY INFRA exclusivamente y límite por déficit en la manga cripto post-compra; presupuesto sobrante en USDT.
- Balancer SELL secuencial SOBRE primero. Capacidad por Exchange libre y Tier T1 30%, T2 70%, T3 100% con deducción de reservas SELL, BTC NEVER SELL.
- Órdenes reutiliza capacidad de venta del Balancer y mantiene independientes el Balance de la elegibilidad estructural Fibonacci. Fase 1: SOLO PROPUESTAS.
- Ventas usa su optimizador JS de dos etapas, objetivo USDT configurable (40% por defecto), contrastado numéricamente contra el módulo Python de SOBRE.
- Semáforos centralizados con banda aprobada del MASTER; TradingBot limitado al universo T1 aprobado.
- Histórico, custodias, Forecast, Compras, Pivotes, Alertas y BTC equivalente conservados.
- No se infieren fills, reservas privadas ni movimientos físicos. Si Google Sheets/MCP requerido falla, la operación sigue bloqueada.

**Validación local:** pruebas Python, 9 suites JS y parseo de plantillas Jinja. Despliegue y health HTTP vivo de Render no efectuados.
